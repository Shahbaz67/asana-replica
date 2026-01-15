"""
Asana API Documentation Parser

Parses the Asana API Reference HTML pages to extract:
- Path parameters
- Query parameters  
- Body parameters
- Response schemas

Usage:
    python scripts/asana_api_parser.py

Reference: https://developers.asana.com/reference/rest-api-reference
"""

import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import json
import time
import re


@dataclass
class Parameter:
    """Represents an API parameter."""
    name: str
    data_type: str
    required: bool = False
    description: str = ""
    constraints: str = ""  # min/max, pattern, etc.


@dataclass
class ResponseSchema:
    """Represents a response schema."""
    status_code: str
    description: str = ""
    schema: Dict = field(default_factory=dict)


@dataclass
class APIEndpoint:
    """Represents a single API endpoint."""
    name: str
    method: str
    path: str
    description: str = ""
    path_params: List[Parameter] = field(default_factory=list)
    query_params: List[Parameter] = field(default_factory=list)
    body_params: List[Parameter] = field(default_factory=list)
    responses: List[ResponseSchema] = field(default_factory=list)


class AsanaAPIParser:
    """Parser for Asana API documentation."""
    
    BASE_URL = "https://developers.asana.com/reference"
    
    # Projects API endpoints to parse
    PROJECT_ENDPOINTS = [
        ("getprojects", "GET", "/projects"),
        ("createproject", "POST", "/projects"),
        ("getproject", "GET", "/projects/{project_gid}"),
        ("updateproject", "PUT", "/projects/{project_gid}"),
        ("deleteproject", "DELETE", "/projects/{project_gid}"),
        ("duplicateproject", "POST", "/projects/{project_gid}/duplicate"),
        ("getprojectsfortask", "GET", "/tasks/{task_gid}/projects"),
        ("getprojectsforteam", "GET", "/teams/{team_gid}/projects"),
        ("createprojectforteam", "POST", "/teams/{team_gid}/projects"),
        ("getprojectsforworkspace", "GET", "/workspaces/{workspace_gid}/projects"),
        ("createprojectforworkspace", "POST", "/workspaces/{workspace_gid}/projects"),
        ("addcustomfieldtoproject", "POST", "/projects/{project_gid}/addCustomFieldSetting"),
        ("removecustomfieldfromproject", "POST", "/projects/{project_gid}/removeCustomFieldSetting"),
        ("gettaskcountsforproject", "GET", "/projects/{project_gid}/task_counts"),
        ("addmembersforproject", "POST", "/projects/{project_gid}/addMembers"),
        ("removemembersforproject", "POST", "/projects/{project_gid}/removeMembers"),
        ("addfollowersforproject", "POST", "/projects/{project_gid}/addFollowers"),
        ("removefollowersforproject", "POST", "/projects/{project_gid}/removeFollowers"),
        ("projectsaveasstemplate", "POST", "/projects/{project_gid}/saveAsTemplate"),
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def fetch_page(self, endpoint_slug: str) -> Optional[BeautifulSoup]:
        """Fetch and parse an API documentation page."""
        url = f"{self.BASE_URL}/{endpoint_slug}"
        print(f"Fetching: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def parse_parameters(self, soup: BeautifulSoup, param_type: str) -> List[Parameter]:
        """
        Parse parameters from the page.
        
        param_type: 'path', 'query', or 'body'
        """
        params = []
        
        # Find the section header for this param type
        # Looking for headings like "PATH PARAMS", "QUERY PARAMS", "BODY PARAMS"
        heading_text = f"{param_type.upper()} PARAM"
        
        # Find all section headers
        headers = soup.find_all(['h4', 'div'], class_=re.compile(r'APISectionHeader|heading'))
        
        target_section = None
        for header in headers:
            if heading_text in header.get_text().upper():
                # Find the next sibling section containing params
                target_section = header.find_next('section') or header.find_next('div', class_=re.compile(r'Param'))
                break
        
        if not target_section:
            # Alternative: look for form groups with param classes
            if param_type == 'body':
                param_containers = soup.find_all('div', class_=re.compile(r'form-group.*field.*Param|Param-expand'))
            else:
                param_containers = soup.find_all('section', class_=re.compile(r'Param-expand'))
        else:
            param_containers = target_section.find_all('div', class_=re.compile(r'Param-header|form-group'))
        
        for container in param_containers:
            param = self._extract_param_from_container(container)
            if param and param.name:
                params.append(param)
        
        return params
    
    def _extract_param_from_container(self, container) -> Optional[Parameter]:
        """Extract parameter details from a container element."""
        try:
            # Extract name
            name_elem = container.find(['label', 'span', 'div'], class_=re.compile(r'Param-name|field-name'))
            name = name_elem.get_text(strip=True) if name_elem else ""
            
            # Extract type
            type_elem = container.find('div', class_=re.compile(r'Param-type|field-type'))
            data_type = type_elem.get_text(strip=True) if type_elem else "string"
            
            # Extract required status
            required_elem = container.find('div', class_=re.compile(r'Param-required'))
            required = bool(required_elem and 'required' in required_elem.get_text().lower())
            
            # Extract constraints (min/max)
            constraints_elem = container.find('div', class_=re.compile(r'Param-minmax'))
            constraints = constraints_elem.get_text(strip=True) if constraints_elem else ""
            
            # Extract description
            desc_elem = container.find('div', class_=re.compile(r'Param-description|field-description'))
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            if name:
                return Parameter(
                    name=name,
                    data_type=data_type,
                    required=required,
                    description=description,
                    constraints=constraints
                )
        except Exception as e:
            print(f"Error extracting param: {e}")
        
        return None
    
    def parse_responses(self, soup: BeautifulSoup) -> List[ResponseSchema]:
        """Parse response schemas from the page."""
        responses = []
        
        # Find response section
        response_section = soup.find('section', class_=re.compile(r'APIResponseSchemaPicker|Accordion'))
        
        if not response_section:
            return responses
        
        # Find all response options (200, 400, 401, etc.)
        response_options = response_section.find_all('div', class_=re.compile(r'AccordionPanel|APIResponseSchemaPicker-option'))
        
        for option in response_options:
            # Get status code
            label = option.find('div', class_=re.compile(r'APIResponseSchemaPicker-label|status-code'))
            status_code = label.get_text(strip=True) if label else "200"
            
            # Get response description/schema
            schema_container = option.find('div', class_=re.compile(r'response-schema|CodeBlock'))
            schema_text = schema_container.get_text(strip=True) if schema_container else ""
            
            responses.append(ResponseSchema(
                status_code=status_code,
                description=schema_text[:200] if schema_text else ""
            ))
        
        return responses
    
    def parse_endpoint(self, endpoint_slug: str, method: str, path: str) -> Optional[APIEndpoint]:
        """Parse a single API endpoint."""
        soup = self.fetch_page(endpoint_slug)
        if not soup:
            return None
        
        # Get endpoint name/title
        title_elem = soup.find('h1') or soup.find('title')
        title = title_elem.get_text(strip=True) if title_elem else endpoint_slug
        
        # Get description
        desc_elem = soup.find('p', class_=re.compile(r'description|intro'))
        description = desc_elem.get_text(strip=True) if desc_elem else ""
        
        endpoint = APIEndpoint(
            name=title,
            method=method,
            path=path,
            description=description,
            path_params=self.parse_parameters(soup, 'path'),
            query_params=self.parse_parameters(soup, 'query'),
            body_params=self.parse_parameters(soup, 'body'),
            responses=self.parse_responses(soup)
        )
        
        return endpoint
    
    def parse_all_project_endpoints(self) -> List[APIEndpoint]:
        """Parse all project-related endpoints."""
        endpoints = []
        
        for slug, method, path in self.PROJECT_ENDPOINTS:
            print(f"\n{'='*60}")
            print(f"Parsing: {method} {path}")
            print(f"{'='*60}")
            
            endpoint = self.parse_endpoint(slug, method, path)
            if endpoint:
                endpoints.append(endpoint)
                self._print_endpoint(endpoint)
            
            # Rate limiting - be nice to their servers
            time.sleep(1)
        
        return endpoints
    
    def _print_endpoint(self, endpoint: APIEndpoint):
        """Pretty print an endpoint's details."""
        print(f"\n📌 {endpoint.name}")
        print(f"   {endpoint.method} {endpoint.path}")
        
        if endpoint.path_params:
            print(f"\n   PATH PARAMS ({len(endpoint.path_params)}):")
            for p in endpoint.path_params:
                req = "✅ required" if p.required else "optional"
                print(f"   - {p.name}: {p.data_type} ({req})")
        
        if endpoint.query_params:
            print(f"\n   QUERY PARAMS ({len(endpoint.query_params)}):")
            for p in endpoint.query_params:
                req = "✅ required" if p.required else "optional"
                print(f"   - {p.name}: {p.data_type} ({req})")
        
        if endpoint.body_params:
            print(f"\n   BODY PARAMS ({len(endpoint.body_params)}):")
            for p in endpoint.body_params:
                req = "✅ required" if p.required else "optional"
                print(f"   - {p.name}: {p.data_type} ({req})")
        
        if endpoint.responses:
            print(f"\n   RESPONSES ({len(endpoint.responses)}):")
            for r in endpoint.responses:
                print(f"   - {r.status_code}")
    
    def export_to_json(self, endpoints: List[APIEndpoint], filename: str):
        """Export parsed endpoints to JSON."""
        data = []
        for ep in endpoints:
            data.append({
                "name": ep.name,
                "method": ep.method,
                "path": ep.path,
                "description": ep.description,
                "path_params": [
                    {"name": p.name, "type": p.data_type, "required": p.required, "description": p.description}
                    for p in ep.path_params
                ],
                "query_params": [
                    {"name": p.name, "type": p.data_type, "required": p.required, "description": p.description}
                    for p in ep.query_params
                ],
                "body_params": [
                    {"name": p.name, "type": p.data_type, "required": p.required, "description": p.description}
                    for p in ep.body_params
                ],
                "responses": [
                    {"status_code": r.status_code, "description": r.description}
                    for r in ep.responses
                ]
            })
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n✅ Exported to {filename}")


def main():
    """Main entry point."""
    print("=" * 60)
    print("🔍 Asana API Documentation Parser")
    print("   Parsing Projects API endpoints...")
    print("=" * 60)
    
    parser = AsanaAPIParser()
    endpoints = parser.parse_all_project_endpoints()
    
    # Export to JSON
    parser.export_to_json(endpoints, "scripts/projects_api_schema.json")
    
    print("\n" + "=" * 60)
    print(f"✅ Parsed {len(endpoints)} endpoints")
    print("=" * 60)


if __name__ == "__main__":
    main()

