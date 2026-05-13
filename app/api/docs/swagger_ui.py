"""
Swagger UI Service
Provides interactive API documentation interface
"""

from flask import Blueprint, render_template, jsonify, request
from flask import current_app
import json
from typing import Dict, Any, Optional

from .openapi import OpenAPIService

class SwaggerUIService:
    """Swagger UI service for interactive API documentation"""
    
    def __init__(self, openapi_service: OpenAPIService):
        """Initialize Swagger UI service"""
        self.openapi_service = openapi_service
        self.config = {
            'dom_id': '#swagger-ui',
            'url': '/api/docs/openapi.json',
            'layout': 'StandaloneLayout',
            'deepLinking': True,
            'displayRequestDuration': True,
            'docExpansion': 'none',
            'operationsSorter': 'alpha',
            'filter': True,
            'showExtensions': True,
            'showCommonExtensions': True,
            'tryItOutEnabled': True
        }
    
    def get_swagger_html(self) -> str:
        """Get Swagger UI HTML page"""
        return render_template('swagger_ui.html', 
                             config=self.config,
                             title=self.openapi_service.title)
    
    def get_openapi_json(self) -> Dict[str, Any]:
        """Get OpenAPI specification as JSON"""
        return self.openapi_service.get_spec()
    
    def get_openapi_yaml(self) -> str:
        """Get OpenAPI specification as YAML"""
        try:
            import yaml
            return yaml.dump(self.openapi_service.get_spec(), default_flow_style=False)
        except ImportError:
            # If PyYAML is not available, return JSON as fallback
            return json.dumps(self.openapi_service.get_spec(), indent=2)
    
    def update_config(self, **kwargs):
        """Update Swagger UI configuration"""
        self.config.update(kwargs)
    
    def set_theme(self, theme: str):
        """Set Swagger UI theme"""
        theme_configs = {
            'dark': {
                'theme': 'dark',
                'bg_color': '#1a1a1a',
                'text_color': '#ffffff'
            },
            'light': {
                'theme': 'light',
                'bg_color': '#ffffff',
                'text_color': '#000000'
            },
            'material': {
                'theme': 'material',
                'bg_color': '#f5f5f5',
                'text_color': '#333333'
            }
        }
        
        if theme in theme_configs:
            self.config.update(theme_configs[theme])
    
    def customize_for_endpoint(self, endpoint_path: str, customization: Dict[str, Any]):
        """Add customization for specific endpoint"""
        if 'customizations' not in self.config:
            self.config['customizations'] = {}
        
        self.config['customizations'][endpoint_path] = customization
    
    def add_custom_css(self, css: str):
        """Add custom CSS to Swagger UI"""
        if 'custom_css' not in self.config:
            self.config['custom_css'] = []
        
        self.config['custom_css'].append(css)
    
    def add_custom_js(self, js: str):
        """Add custom JavaScript to Swagger UI"""
        if 'custom_js' not in self.config:
            self.config['custom_js'] = []
        
        self.config['custom_js'].append(js)
    
    def get_config_json(self) -> str:
        """Get Swagger UI configuration as JSON"""
        return json.dumps(self.config)
    
    def validate_openapi_spec(self) -> Dict[str, Any]:
        """Validate OpenAPI specification"""
        return self.openapi_service.validate_spec()
    
    def get_api_info(self) -> Dict[str, Any]:
        """Get API information summary"""
        spec = self.openapi_service.get_spec()
        
        return {
            'title': spec['info']['title'],
            'version': spec['info']['version'],
            'description': spec['info'].get('description', ''),
            'contact': spec['info'].get('contact', {}),
            'license': spec['info'].get('license', {}),
            'servers': spec.get('servers', []),
            'paths_count': len(spec.get('paths', {})),
            'schemas_count': len(spec.get('components', {}).get('schemas', {})),
            'security_schemes_count': len(spec.get('components', {}).get('securitySchemes', {})),
            'tags_count': len(spec.get('tags', []))
        }
    
    def search_endpoints(self, query: str) -> List[Dict[str, Any]]:
        """Search endpoints by query"""
        spec = self.openapi_service.get_spec()
        results = []
        
        query_lower = query.lower()
        
        for path, path_item in spec.get('paths', {}).items():
            for method, operation in path_item.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
                    # Search in operation ID, summary, description, and tags
                    searchable_text = [
                        operation.get('operationId', ''),
                        operation.get('summary', ''),
                        operation.get('description', ''),
                        ' '.join(operation.get('tags', [])),
                        path
                    ]
                    
                    if any(query_lower in text.lower() for text in searchable_text):
                        results.append({
                            'path': path,
                            'method': method.upper(),
                            'operationId': operation.get('operationId', ''),
                            'summary': operation.get('summary', ''),
                            'tags': operation.get('tags', []),
                            'description': operation.get('description', '')[:200] + '...' if len(operation.get('description', '')) > 200 else operation.get('description', '')
                        })
        
        return results
    
    def get_endpoint_details(self, path: str, method: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific endpoint"""
        spec = self.openapi_service.get_spec()
        
        path_item = spec.get('paths', {}).get(path)
        if not path_item:
            return None
        
        operation = path_item.get(method.lower())
        if not operation:
            return None
        
        return {
            'path': path,
            'method': method.upper(),
            'operationId': operation.get('operationId', ''),
            'summary': operation.get('summary', ''),
            'description': operation.get('description', ''),
            'tags': operation.get('tags', []),
            'parameters': operation.get('parameters', []),
            'requestBody': operation.get('requestBody', {}),
            'responses': operation.get('responses', {}),
            'security': operation.get('security', []),
            'deprecated': operation.get('deprecated', False)
        }
    
    def get_schema_details(self, schema_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific schema"""
        spec = self.openapi_service.get_spec()
        
        schemas = spec.get('components', {}).get('schemas', {})
        if schema_name not in schemas:
            return None
        
        schema = schemas[schema_name]
        
        return {
            'name': schema_name,
            'type': schema.get('type', 'object'),
            'properties': schema.get('properties', {}),
            'required': schema.get('required', []),
            'additionalProperties': schema.get('additionalProperties', True),
            'description': schema.get('description', ''),
            'example': schema.get('example', None)
        }
    
    def export_specification(self, format: str = 'json') -> str:
        """Export OpenAPI specification in specified format"""
        if format.lower() == 'json':
            return self.openapi_service.get_spec_json()
        elif format.lower() == 'yaml':
            return self.get_openapi_yaml()
        else:
            raise ValueError(f"Unsupported format: {format}. Supported formats: json, yaml")
    
    def generate_client_code(self, language: str, endpoint_path: str, method: str) -> Optional[str]:
        """Generate client code for specific endpoint"""
        details = self.get_endpoint_details(endpoint_path, method)
        if not details:
            return None
        
        if language.lower() == 'javascript':
            return self._generate_javascript_client(details)
        elif language.lower() == 'python':
            return self._generate_python_client(details)
        elif language.lower() == 'curl':
            return self._generate_curl_client(details)
        else:
            raise ValueError(f"Unsupported language: {language}. Supported languages: javascript, python, curl")
    
    def _generate_javascript_client(self, details: Dict[str, Any]) -> str:
        """Generate JavaScript client code"""
        method = details['method'].lower()
        url = f"`{details['path']}`"
        
        # Extract parameters
        params = []
        for param in details.get('parameters', []):
            if param['in'] == 'path':
                url = url.replace(f"{{{param['name']}}}", f"${{param['name']}}")
            elif param['in'] == 'query':
                params.append(f"  {param['name']}: null")
        
        param_names = [p['name'] for p in details.get('parameters', []) if p['in'] in ['path', 'query']]
        param_list = ', '.join(param_names)
        example_params = ', '.join([f"'{p}'" for p in param_names])
        
        code = f"""
//# {details['summary']}
async function {details['operationId'] or 'apiCall'}({param_list}) {{
  const url = {url};
  
  const options = {{
    method: '{method}',
    headers: {{
      'Content-Type': 'application/json',
      // Add your authentication headers here
    }}
  }};
  
  if ({method} !== 'get') {{
    options.body = JSON.stringify({{
      // Add your request body here
    }});
  }}
  
  try {{
    const response = await fetch(url, options);
    const data = await response.json();
    return data;
  }} catch (error) {{
    console.error('API call failed:', error);
    throw error;
  }}
}}

// Example usage:
// {details['operationId'] or 'apiCall'}({example_params})
"""
        return code.strip()
    
    def _generate_python_client(self, details: Dict[str, Any]) -> str:
        """Generate Python client code"""
        method = details['method'].lower()
        url = details['path']
        
        # Extract parameters
        params = []
        path_params = []
        query_params = []
        
        for param in details.get('parameters', []):
            if param['in'] == 'path':
                path_params.append(param['name'])
                url = url.replace(f"{{{param['name']}}}", f"{{{param['name']}}}")
            elif param['in'] == 'query':
                query_params.append(param['name'])
        
        # Prepare parameter strings
        python_param_names = [p['name'] for p in details.get('parameters', []) if p['in'] in ['path', 'query']]
        python_param_list = ', '.join(python_param_names)
        
        path_param_assignments = ', '.join([f"{p}={p}" for p in path_params])
        query_param_assignments = ', '.join([f"'{p}': {p}" for p in query_params])
        example_assignments = ', '.join([f"{p}='value'" for p in (path_params + query_params)])
        
        url_format_line = f"url = url.format({path_param_assignments})" if path_params else "# No path parameters"
        params_line = f"params = {{{query_param_assignments}}}" if query_params else "params = {}"
        
        code = f"""
import requests
import json

# {details['summary']}
def {details['operationId'] or 'api_call'}({python_param_list}):
    \"\"\"
    {details['description']}
    \"\"\"
    
    url = "{url}"
    
    # Format URL with path parameters
    {url_format_line}
    
    # Prepare query parameters
    {params_line}
    
    headers = {{
        'Content-Type': 'application/json',
        # Add your authentication headers here
    }}
    
    try:
        if {method} == 'get':
            response = requests.get(url, params=params, headers=headers)
        elif {method} == 'post':
            response = requests.post(url, params=params, headers=headers, json={{}})
            # Add your request body here
        elif {method} == 'put':
            response = requests.put(url, params=params, headers=headers, json={{}})
            # Add your request body here
        elif {method} == 'delete':
            response = requests.delete(url, params=params, headers=headers)
        else:
            response = requests.request({method}, url, params=params, headers=headers)
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"API call failed: {{e}}")
        raise

# Example usage:
# {details['operationId'] or 'api_call'}({example_assignments})
"""
        return code.strip()
    
    def _generate_curl_client(self, details: Dict[str, Any]) -> str:
        """Generate cURL command"""
        method = details['method'].upper()
        url = details['path']
        
        # Extract parameters
        for param in details.get('parameters', []):
            if param['in'] == 'path':
                url = url.replace(f"{{{param['name']}}}", f"<{param['name']}>")
        
        curl_parts = [f"curl -X {method}"]
        curl_parts.append(f"'{url}'")
        curl_parts.append("-H 'Content-Type: application/json'")
        curl_parts.append("-H 'Authorization: Bearer <your-token>'")
        
        if method not in ['GET', 'HEAD']:
            curl_parts.append("-d '{\"key\": \"value\"}'  # Add your request body here")
        
        return " \\\n  ".join(curl_parts)


def create_swagger_ui_service(openapi_service: OpenAPIService) -> SwaggerUIService:
    """Create and initialize Swagger UI service"""
    return SwaggerUIService(openapi_service)
