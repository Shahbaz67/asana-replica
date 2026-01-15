"""
Asana Project API Schema Extractor

Extracts all parameters and response schemas from Asana's project endpoints
using Playwright for browser automation.

Usage:
    pip install playwright
    playwright install chromium
    python scripts/extract_project_schemas.py
"""

import asyncio
import json
import re
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict
from playwright.async_api import async_playwright, Page


@dataclass
class Parameter:
    name: str
    data_type: str
    required: bool = False
    deprecated: bool = False
    description: str = ""
    enum_values: List[str] = field(default_factory=list)
    create_only: bool = False


@dataclass
class ResponseField:
    name: str
    data_type: str
    description: str = ""
    nested_fields: List['ResponseField'] = field(default_factory=list)


@dataclass
class APIEndpoint:
    name: str
    method: str
    path: str
    description: str = ""
    scope: str = ""
    path_params: List[Parameter] = field(default_factory=list)
    query_params: List[Parameter] = field(default_factory=list)
    body_params: List[Parameter] = field(default_factory=list)
    response_codes: List[str] = field(default_factory=list)
    response_fields: List[ResponseField] = field(default_factory=list)


# All project-related endpoints
PROJECT_ENDPOINTS = [
    # Core Project CRUD
    ("getprojects", "GET", "/projects"),
    ("createproject", "POST", "/projects"),
    ("getproject", "GET", "/projects/{project_gid}"),
    ("updateproject", "PUT", "/projects/{project_gid}"),
    ("deleteproject", "DELETE", "/projects/{project_gid}"),
    ("duplicateproject", "POST", "/projects/{project_gid}/duplicate"),
    
    # Project by context
    ("getprojectsfortask", "GET", "/tasks/{task_gid}/projects"),
    ("getprojectsforteam", "GET", "/teams/{team_gid}/projects"),
    ("createprojectforteam", "POST", "/teams/{team_gid}/projects"),
    ("getprojectsforworkspace", "GET", "/workspaces/{workspace_gid}/projects"),
    ("createprojectforworkspace", "POST", "/workspaces/{workspace_gid}/projects"),
    
    # Project actions
    ("addcustomfieldsettingforproject", "POST", "/projects/{project_gid}/addCustomFieldSetting"),
    ("removecustomfieldsettingforproject", "POST", "/projects/{project_gid}/removeCustomFieldSetting"),
    ("gettaskcountsforproject", "GET", "/projects/{project_gid}/task_counts"),
    ("addmembersforproject", "POST", "/projects/{project_gid}/addMembers"),
    ("removemembersforproject", "POST", "/projects/{project_gid}/removeMembers"),
    ("addfollowersforproject", "POST", "/projects/{project_gid}/addFollowers"),
    ("removefollowersforproject", "POST", "/projects/{project_gid}/removeFollowers"),
    ("projectsaveasstemplate", "POST", "/projects/{project_gid}/saveAsTemplate"),
]


class AsanaSchemaExtractor:
    def __init__(self):
        self.base_url = "https://developers.asana.com/reference"
        self.endpoints: List[APIEndpoint] = []
    
    async def extract_all(self):
        """Extract schemas from all project endpoints."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            for slug, method, path in PROJECT_ENDPOINTS:
                print(f"\n{'='*60}")
                print(f"Extracting: {method} {path}")
                print(f"{'='*60}")
                
                endpoint = await self.extract_endpoint(page, slug, method, path)
                if endpoint:
                    self.endpoints.append(endpoint)
                    self._print_endpoint(endpoint)
                
                await asyncio.sleep(1)  # Rate limiting
            
            await browser.close()
        
        return self.endpoints
    
    async def extract_endpoint(self, page: Page, slug: str, method: str, path: str) -> Optional[APIEndpoint]:
        """Extract schema from a single endpoint page."""
        url = f"{self.base_url}/{slug}"
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)  # Wait for JS rendering
            
            # Get page title
            title = await page.title()
            
            # Get description
            desc_elem = await page.query_selector("article p")
            description = await desc_elem.inner_text() if desc_elem else ""
            
            # Get required scope
            scope_elem = await page.query_selector("code")
            scope = await scope_elem.inner_text() if scope_elem else ""
            
            endpoint = APIEndpoint(
                name=title,
                method=method,
                path=path,
                description=description[:200] if description else "",
                scope=scope
            )
            
            # Extract path params
            endpoint.path_params = await self._extract_params(page, "Path Params")
            
            # Extract query params
            endpoint.query_params = await self._extract_params(page, "Query Params")
            
            # Extract body params (need to expand the data object)
            if method in ["POST", "PUT", "PATCH"]:
                # Click to expand body params if present
                try:
                    expand_btn = await page.query_selector('button:has-text("data object")')
                    if expand_btn:
                        await expand_btn.click()
                        await page.wait_for_timeout(500)
                except:
                    pass
                
                endpoint.body_params = await self._extract_body_params(page)
            
            # Extract response codes
            endpoint.response_codes = await self._extract_response_codes(page)
            
            return endpoint
            
        except Exception as e:
            print(f"Error extracting {slug}: {e}")
            return None
    
    async def _extract_params(self, page: Page, section_name: str) -> List[Parameter]:
        """Extract parameters from a named section."""
        params = []
        
        try:
            # Find the section by looking for the header text
            sections = await page.query_selector_all("generic")
            
            for section in sections:
                text = await section.inner_text()
                if section_name in text:
                    # Get all parameter rows in this section
                    param_rows = await section.query_selector_all("[class*='Param']")
                    
                    for row in param_rows:
                        param = await self._extract_param_from_row(row)
                        if param and param.name:
                            params.append(param)
                    break
        except:
            pass
        
        return params
    
    async def _extract_body_params(self, page: Page) -> List[Parameter]:
        """Extract body parameters after expanding the data object."""
        params = []
        
        try:
            # Look for all form fields in the body params section
            param_elements = await page.query_selector_all('[class*="form-group"], [class*="Param-header"]')
            
            for elem in param_elements:
                try:
                    # Get name
                    name_elem = await elem.query_selector('[class*="Param-name"], label')
                    name = await name_elem.inner_text() if name_elem else ""
                    name = name.strip()
                    
                    if not name or name in ["data", "object"]:
                        continue
                    
                    # Get type
                    type_elem = await elem.query_selector('[class*="Param-type"]')
                    data_type = await type_elem.inner_text() if type_elem else "string"
                    data_type = data_type.strip()
                    
                    # Check for required
                    required_elem = await elem.query_selector('[class*="required"]')
                    required = bool(required_elem)
                    
                    # Check for deprecated
                    deprecated_elem = await elem.query_selector('[class*="deprecated"]')
                    deprecated = bool(deprecated_elem)
                    
                    # Get description
                    desc_elem = await elem.query_selector('p, [class*="description"]')
                    description = await desc_elem.inner_text() if desc_elem else ""
                    description = description[:200].strip()
                    
                    # Check for Create-only
                    create_only = "Create-only" in description or "create-only" in description.lower()
                    
                    # Get enum values
                    enum_values = []
                    enum_elems = await elem.query_selector_all('option, code')
                    for enum_elem in enum_elems:
                        val = await enum_elem.inner_text()
                        val = val.strip()
                        if val and val not in ["", "true", "false"]:
                            enum_values.append(val)
                    
                    params.append(Parameter(
                        name=name,
                        data_type=data_type,
                        required=required,
                        deprecated=deprecated,
                        description=description,
                        enum_values=enum_values[:10] if enum_values else [],
                        create_only=create_only
                    ))
                except:
                    continue
        except Exception as e:
            print(f"Error extracting body params: {e}")
        
        return params
    
    async def _extract_param_from_row(self, row) -> Optional[Parameter]:
        """Extract a single parameter from a row element."""
        try:
            name_elem = await row.query_selector('[class*="name"], label')
            name = await name_elem.inner_text() if name_elem else ""
            
            type_elem = await row.query_selector('[class*="type"]')
            data_type = await type_elem.inner_text() if type_elem else "string"
            
            required_elem = await row.query_selector('[class*="required"]')
            required = bool(required_elem)
            
            desc_elem = await row.query_selector('p')
            description = await desc_elem.inner_text() if desc_elem else ""
            
            return Parameter(
                name=name.strip(),
                data_type=data_type.strip(),
                required=required,
                description=description[:200].strip()
            )
        except:
            return None
    
    async def _extract_response_codes(self, page: Page) -> List[str]:
        """Extract response status codes."""
        codes = []
        try:
            code_elems = await page.query_selector_all('[class*="ResponseSchemaPicker"] code, [class*="status-code"]')
            for elem in code_elems:
                code = await elem.inner_text()
                code = code.strip()
                if code.isdigit():
                    codes.append(code)
        except:
            pass
        return list(set(codes))
    
    def _print_endpoint(self, ep: APIEndpoint):
        """Print endpoint details."""
        print(f"\n📌 {ep.name}")
        print(f"   {ep.method} {ep.path}")
        print(f"   Scope: {ep.scope}")
        
        if ep.path_params:
            print(f"\n   PATH PARAMS ({len(ep.path_params)}):")
            for p in ep.path_params:
                req = "✅ required" if p.required else "optional"
                print(f"   - {p.name}: {p.data_type} ({req})")
        
        if ep.query_params:
            print(f"\n   QUERY PARAMS ({len(ep.query_params)}):")
            for p in ep.query_params:
                req = "✅ required" if p.required else "optional"
                print(f"   - {p.name}: {p.data_type} ({req})")
        
        if ep.body_params:
            print(f"\n   BODY PARAMS ({len(ep.body_params)}):")
            for p in ep.body_params:
                req = "✅ required" if p.required else ""
                dep = "⚠️ deprecated" if p.deprecated else ""
                print(f"   - {p.name}: {p.data_type} {req} {dep}".strip())
        
        if ep.response_codes:
            print(f"\n   RESPONSES: {', '.join(ep.response_codes)}")
    
    def export_to_json(self, filename: str):
        """Export all endpoints to JSON."""
        data = []
        for ep in self.endpoints:
            data.append({
                "name": ep.name,
                "method": ep.method,
                "path": ep.path,
                "description": ep.description,
                "scope": ep.scope,
                "path_params": [asdict(p) for p in ep.path_params],
                "query_params": [asdict(p) for p in ep.query_params],
                "body_params": [asdict(p) for p in ep.body_params],
                "response_codes": ep.response_codes
            })
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n✅ Exported to {filename}")


async def main():
    print("=" * 60)
    print("🔍 Asana Project API Schema Extractor")
    print("=" * 60)
    
    extractor = AsanaSchemaExtractor()
    endpoints = await extractor.extract_all()
    
    # Export to JSON
    extractor.export_to_json("scripts/project_endpoints_schema.json")
    
    print("\n" + "=" * 60)
    print(f"✅ Extracted {len(endpoints)} endpoints")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

