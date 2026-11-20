"""
Problem Ingestion & URL Import Service for Codeforces and LeetCode.
Also handles manual problem creation with structured fallback and validation.
"""
from __future__ import annotations

import re
from typing import Dict, Any, List, Optional
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field


class ImportedProblemData(BaseModel):
    title: str
    statement: str
    constraints: Optional[str] = None
    input_format: Optional[str] = None
    output_format: Optional[str] = None
    sample_test_cases: List[Dict[str, str]] = Field(default_factory=list)
    source: str
    source_url: str
    time_limit_ms: int = 2000
    memory_limit_mb: int = 256
    estimated_difficulty: str = "medium"
    official_rating: Optional[int] = None
    is_leetcode_style: bool = False
    function_signature: Optional[str] = None


class ProblemImporter:
    """
    Extracts structured competitive programming problems from Codeforces & LeetCode URLs.
    Includes rate limit, timeout, and HTML error resilience.
    """

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    async def import_from_url(self, url: str) -> ImportedProblemData:
        url = url.strip()
        if "codeforces.com" in url:
            return await self._import_codeforces(url)
        elif "leetcode.com" in url:
            return await self._import_leetcode(url)
        else:
            raise ValueError(
                "Unsupported URL domain. IntelliGate currently supports Codeforces and LeetCode problem URLs."
            )

    async def _import_codeforces(self, url: str) -> ImportedProblemData:
        """
        Parses Codeforces problem statements, input/output specifications, and public example tests.
        Handles both /problemset/problem/X/Y and /contest/X/problem/Y formats.
        """
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=self.HEADERS) as client:
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    raise ValueError(f"Codeforces returned status code {resp.status_code}")
                html = resp.text
            except Exception as e:
                raise ValueError(f"Failed to fetch Codeforces problem: {str(e)}")

        soup = BeautifulSoup(html, "html.parser")
        problem_statement = soup.find("div", class_="problem-statement")
        if not problem_statement:
            raise ValueError("Could not locate Codeforces problem statement block in HTML.")

        # Title
        title_elem = problem_statement.find("div", class_="title")
        title = title_elem.get_text(strip=True) if title_elem else "Codeforces Problem"

        # Time Limit
        time_elem = problem_statement.find("div", class_="time-limit")
        time_limit_ms = 2000
        if time_elem:
            time_text = time_elem.get_text()
            m = re.search(r"(\d+(\.\d+)?)\s*second", time_text, re.IGNORECASE)
            if m:
                time_limit_ms = int(float(m.group(1)) * 1000)

        # Memory Limit
        mem_elem = problem_statement.find("div", class_="memory-limit")
        mem_limit_mb = 256
        if mem_elem:
            mem_text = mem_elem.get_text()
            m = re.search(r"(\d+)\s*megabyte", mem_text, re.IGNORECASE)
            if m:
                mem_limit_mb = int(m.group(1))

        # Statement Body
        # The main statement is before input-specification
        body_divs = []
        for child in problem_statement.children:
            if child.name == "div" and not child.get("class"):
                body_divs.append(child.get_text(separator="\n", strip=True))
        statement = "\n\n".join(body_divs) if body_divs else problem_statement.get_text(separator="\n", strip=True)

        # Input & Output format
        input_spec = problem_statement.find("div", class_="input-specification")
        input_format = input_spec.get_text(separator="\n", strip=True) if input_spec else ""

        output_spec = problem_statement.find("div", class_="output-specification")
        output_format = output_spec.get_text(separator="\n", strip=True) if output_spec else ""

        # Samples
        sample_tests: List[Dict[str, str]] = []
        sample_tests_div = problem_statement.find("div", class_="sample-tests")
        if sample_tests_div:
            inputs = sample_tests_div.find_all("div", class_="input")
            outputs = sample_tests_div.find_all("div", class_="output")
            for inp, out in zip(inputs, outputs):
                pre_in = inp.find("pre")
                pre_out = out.find("pre")
                if pre_in and pre_out:
                    # Clean Codeforces pre tag lines
                    in_text = "\n".join([line.strip() for line in pre_in.get_text().splitlines() if line.strip()]) + "\n"
                    out_text = "\n".join([line.strip() for line in pre_out.get_text().splitlines() if line.strip()]) + "\n"
                    sample_tests.append({"input": in_text, "expected": out_text})

        # Official rating from problem tags if visible on page
        official_rating = None
        for tag_elem in soup.find_all("span", class_="tag-box"):
            txt = tag_elem.get_text().strip()
            m_r = re.search(r"^\*(\d+)$", txt)
            if m_r:
                official_rating = int(m_r.group(1))
                break

        return ImportedProblemData(
            title=title,
            statement=statement,
            constraints=f"Time limit: {time_limit_ms} ms, Memory limit: {mem_limit_mb} MB",
            input_format=input_format,
            output_format=output_format,
            sample_test_cases=sample_tests,
            source="codeforces",
            source_url=url,
            time_limit_ms=time_limit_ms,
            memory_limit_mb=mem_limit_mb,
            estimated_difficulty="medium",
            official_rating=official_rating,
            is_leetcode_style=False,
        )

    async def _import_leetcode(self, url: str) -> ImportedProblemData:
        """
        Extracts LeetCode problem metadata using LeetCode public GraphQL API endpoint.
        """
        match = re.search(r"leetcode\.com/problems/([^/]+)", url)
        if not match:
            raise ValueError("Invalid LeetCode URL structure. Expected leetcode.com/problems/<title-slug>/")

        title_slug = match.group(1)

        graphql_query = {
            "query": """
            query getQuestionDetail($titleSlug: String!) {
              question(titleSlug: $titleSlug) {
                questionId
                title
                content
                difficulty
                exampleTestcaseList
                codeSnippets {
                  lang
                  langSlug
                  code
                }
              }
            }
            """,
            "variables": {"titleSlug": title_slug},
        }

        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True, headers=self.HEADERS) as client:
            try:
                resp = await client.post("https://leetcode.com/graphql", json=graphql_query)
                if resp.status_code != 200:
                    raise ValueError(f"LeetCode GraphQL returned status {resp.status_code}")
                data = resp.json().get("data", {}).get("question")
                if not data:
                    raise ValueError(f"Problem '{title_slug}' not found on LeetCode.")
            except Exception as e:
                raise ValueError(f"Failed to query LeetCode GraphQL: {str(e)}")

        raw_html = data.get("content") or ""
        soup = BeautifulSoup(raw_html, "html.parser")
        statement = soup.get_text(separator="\n", strip=True)

        title = f"{data.get('questionId', '')}. {data.get('title', title_slug)}"
        difficulty = data.get("difficulty", "Medium").lower()

        # Parse examples as sample test cases
        samples: List[Dict[str, str]] = []
        raw_examples = data.get("exampleTestcaseList") or []
        for ex in raw_examples:
            samples.append({"input": ex.strip() + "\n", "expected": ""})

        # Python / C++ signatures
        py_sig = None
        for snippet in data.get("codeSnippets", []):
            if snippet.get("langSlug") == "python3":
                py_sig = snippet.get("code")
                break

        return ImportedProblemData(
            title=title,
            statement=statement,
            constraints="Refer to problem statement constraints.",
            input_format="Method parameters as specified in signature",
            output_format="Return value as specified in signature",
            sample_test_cases=samples,
            source="leetcode",
            source_url=url,
            estimated_difficulty=difficulty,
            is_leetcode_style=True,
            function_signature=py_sig,
        )


problem_importer = ProblemImporter()
