"""
Redis Lua scripts for distributed rate limiting and atomic budget reservation/settlement.
"""
from __future__ import annotations

# 1. Sliding-window rate limiter
# KEYS[1]: Rate limit key
# ARGV[1]: Limit (integer)
# ARGV[2]: Window in seconds (float/integer)
# ARGV[3]: Current timestamp (float)
# Returns: [allowed: 0 or 1, retry_after_seconds: integer, current_count: integer]
SLIDING_WINDOW_RATE_LIMIT_LUA = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local window_start = now - window

redis.call('ZREMRANGEBYSCORE', key, 0, window_start)
local count = redis.call('ZCARD', key)
if count >= limit then
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retry_after = 1
    if oldest and #oldest >= 2 then
        retry_after = math.ceil(tonumber(oldest[2]) + window - now)
        if retry_after < 1 then retry_after = 1 end
    end
    return {0, retry_after, count}
end

redis.call('ZADD', key, now, tostring(now) .. '-' .. tostring(math.random(1000000)))
redis.call('EXPIRE', key, math.ceil(window) + 60)
return {1, 0, count + 1}
"""

# 2. Atomic budget reservation
# KEYS[1]: Budget hash key (e.g. budget:org:<org_id>:monthly:<date>)
# ARGV[1]: Total budget limit USD (float)
# ARGV[2]: Amount to reserve USD (float)
# ARGV[3]: Reservation ID (string UUID)
# Returns: [success: 1 or 0, remaining_or_available: float]
BUDGET_RESERVE_LUA = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local amount = tonumber(ARGV[2])
local reservation_id = ARGV[3]

local used = tonumber(redis.call('HGET', key, 'used') or '0')
local reserved = tonumber(redis.call('HGET', key, 'reserved') or '0')
local total_committed = used + reserved

if total_committed + amount > limit then
    return {0, limit - total_committed}
end

redis.call('HSET', key, 'reserved_' .. reservation_id, tostring(amount))
redis.call('HINCRBYFLOAT', key, 'reserved', amount)
redis.call('EXPIRE', key, 86400 * 35)
return {1, limit - total_committed - amount}
"""

# 3. Atomic budget settlement (idempotent)
# KEYS[1]: Budget hash key
# ARGV[1]: Reservation ID (string UUID)
# ARGV[2]: Actual cost USD (float)
# Returns: 1 if settled, 0 if already settled or not found
BUDGET_SETTLE_LUA = """
local key = KEYS[1]
local reservation_id = ARGV[1]
local actual_cost = tonumber(ARGV[2])

local reserved_amount = tonumber(redis.call('HGET', key, 'reserved_' .. reservation_id) or '0')
if reserved_amount <= 0 then
    return 0
end

redis.call('HINCRBYFLOAT', key, 'reserved', -reserved_amount)
redis.call('HINCRBYFLOAT', key, 'used', actual_cost)
redis.call('HDEL', key, 'reserved_' .. reservation_id)
return 1
"""

# 4. Atomic release of unused reservation
# KEYS[1]: Budget hash key
# ARGV[1]: Reservation ID (string UUID)
# Returns: 1 if released, 0 if not found
BUDGET_RELEASE_LUA = """
local key = KEYS[1]
local reservation_id = ARGV[1]

local reserved_amount = tonumber(redis.call('HGET', key, 'reserved_' .. reservation_id) or '0')
if reserved_amount <= 0 then
    return 0
end

redis.call('HINCRBYFLOAT', key, 'reserved', -reserved_amount)
redis.call('HDEL', key, 'reserved_' .. reservation_id)
return 1
"""

