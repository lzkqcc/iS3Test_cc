import os
import sys
import importlib
import inspect
import traceback
from typing import Dict, Any, List, Tuple


class Initializer:
    def __init__(self, enabled_tools: List[str] = [], model_string: str = None):
        self.toolbox_metadata = {}
        self.available_tools = []
        self.enabled_tools = enabled_tools
        self.model_string = model_string # llm model string

        print("\nInitializing OpenTools...")
        print(f"Enabled tools: {self.enabled_tools}")
        print(f"LLM model string: {self.model_string}")
        self._set_up_tools()

    def get_project_root(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        while current_dir != '/':
            if os.path.exists(os.path.join(current_dir, 'opentools')):
                return os.path.join(current_dir, 'opentools')
            current_dir = os.path.dirname(current_dir)
        raise Exception("Could not find project root")
        
    def load_tools_and_get_metadata(self) -> Dict[str, Any]:
        # Implementation of load_tools_and_get_metadata function
        print("Loading tools and getting metadata...")
        self.toolbox_metadata = {}
        opentools_dir = self.get_project_root()
        tools_dir = os.path.join(opentools_dir, 'tools')
        
        print(f"OpenTools directory: {opentools_dir}")
        print(f"Tools directory: {tools_dir}")
        
        # Add the OpenTools directory and its parent to the Python path
        sys.path.insert(0, opentools_dir)
        sys.path.insert(0, os.path.dirname(opentools_dir))
        print(f"Updated Python path: {sys.path}")
        
        if not os.path.exists(tools_dir):
            print(f"Error: Tools directory does not exist: {tools_dir}")
            return self.toolbox_metadata

        for root, dirs, files in os.walk(tools_dir):
            # print(f"\nScanning directory: {root}")
            if 'tool.py' in files and os.path.basename(root) in self.available_tools:
                file = 'tool.py'
                module_path = os.path.join(root, file)
                module_name = os.path.splitext(file)[0]
                relative_path = os.path.relpath(module_path, opentools_dir)
                import_path = '.'.join(os.path.split(relative_path)).replace(os.sep, '.')[:-3]

                print(f"\nAttempting to import: {import_path}")
                try:
                    module = importlib.import_module(import_path)
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and name.endswith('Tool') and name != 'BaseTool':
                            print(f"Found tool class: {name}")
                            # print(f"Class attributes: {dir(obj)}")
                            # print(f"Class __dict__: {obj.__dict__}")
                            try:
                                # Check if the tool requires an LLM engine
                                if hasattr(obj, 'require_llm_engine') and obj.require_llm_engine:
                                    tool_instance = obj(model_string=self.model_string)
                                else:
                                    tool_instance = obj()

                                # print(f"\nInstance attributes: {dir(tool_instance)}")
                                # print(f"\nInstance __dict__: {tool_instance.__dict__}")
                                
                                self.toolbox_metadata[name] = {
                                    'tool_name': getattr(tool_instance, 'tool_name', 'Unknown'),
                                    'tool_description': getattr(tool_instance, 'tool_description', 'No description'),
                                    'tool_version': getattr(tool_instance, 'tool_version', 'Unknown'),
                                    'input_types': getattr(tool_instance, 'input_types', {}),
                                    'output_type': getattr(tool_instance, 'output_type', 'Unknown'),
                                    'demo_commands': getattr(tool_instance, 'demo_commands', []),
                                    'user_metadata': getattr(tool_instance, 'user_metadata', {}), # NOTE: This is a placeholder for user-defined metadata
                                    'require_llm_engine': getattr(obj, 'require_llm_engine', False),
                                }
                                print(f"\nMetadata for {name}: {self.toolbox_metadata[name]}")
                            except Exception as e:
                                print(f"Error instantiating {name}: {str(e)}")
                except Exception as e:
                    print(f"Error loading module {module_name}: {str(e)}")
                    
        print(f"\nTotal number of tools loaded: {len(self.toolbox_metadata)}")

        return self.toolbox_metadata

    def run_demo_commands(self) -> List[str]:
        print("\nRunning demo commands for each tool...")
        self.available_tools = []

        for tool_name, tool_data in self.toolbox_metadata.items():
            print(f"\nChecking availability of {tool_name}...")

            try:
                # Import the tool module
                module_name = f"tools.{tool_name.lower().replace('_tool', '')}.tool"
                module = importlib.import_module(module_name)

                # Get the tool class
                tool_class = getattr(module, tool_name)

                # Instantiate the tool
                tool_instance = tool_class()

                # FIXME This is a temporary workaround to avoid running demo commands
                self.available_tools.append(tool_name)

                # # TODO Run the first demo command if available
                # demo_commands = tool_data.get('demo_commands', [])
                # if demo_commands:
                #     print(f"Running demo command: {demo_commands[0]['command']}")
                #     # Extract the arguments from the demo command
                #     command = demo_commands[0]['command']
                #     args_start = command.index('(') + 1
                #     args_end = command.rindex(')')
                #     args_str = command[args_start:args_end]

                #     # Create a dictionary of arguments
                #     args_dict = eval(f"dict({args_str})")

                #     # Execute the demo command
                #     result = tool_instance.execute(**args_dict)
                #     print(f"Demo command executed successfully. Result: {result}")

                #     self.available_tools.append(tool_name)
                # else:
                #     print(f"No demo commands available for {tool_name}")
                #     # If no demo commands, we'll assume the tool is available
                #     self.available_tools.append(tool_name)

            except Exception as e:
                print(f"Error checking availability of {tool_name}: {str(e)}")
                print(traceback.format_exc())

        # update the toolmetadata with the available tools
        self.toolbox_metadata = {tool: self.toolbox_metadata[tool] for tool in self.available_tools}
        print(f"\nUpdated total number of available tools: {len(self.toolbox_metadata)}")
        print(f"\nAvailable tools: {self.available_tools}")

        return self.available_tools
    
    def _set_up_tools(self) -> None:
        print("Setting up tools...")

        # Keep enabled tools
        self.available_tools = [tool.lower().replace('_tool', '') for tool in self.enabled_tools]
        
        # Load tools and get metadata
        self.load_tools_and_get_metadata()
        
        # Run demo commands to determine available tools
        self.run_demo_commands()
        
        # Filter toolbox_metadata to include only available tools
        self.toolbox_metadata = {tool: self.toolbox_metadata[tool] for tool in self.available_tools}
        
        print(f"\nTotal number of available tools: {len(self.available_tools)}")
        print(f"Available tools: {self.available_tools}")
        print(f"Enabled tools: {self.enabled_tools}")


if __name__ == "__main__":
    enabled_tools = ["Generalist_Solution_Generator_Tool"]
    initializer = Initializer(enabled_tools=enabled_tools)

    print("\nAvailable tools:")
    print(initializer.available_tools)

    print("\nToolbox metadata for available tools:")
    print(initializer.toolbox_metadata)
    