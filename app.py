import os
import sys
import json
import argparse
import time
import io
import uuid
from PIL import Image
from typing import List, Dict, Any, Iterator
import gradio as gr

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.insert(0, project_root)

from opentools.models.initializer import Initializer
from opentools.models.planner import Planner
from opentools.models.memory import Memory
from opentools.models.executor import Executor
from opentools.models.utlis import make_json_serializable

# solver = None

# class ChatMessage:
#     def __init__(self, role: str, content: str, metadata: dict = None):
#         self.role = role
#         self.content = content
#         self.metadata = metadata or {}

# class Solver:
#     def __init__(
#         self,
#         planner,
#         memory,
#         executor,
#         task: str,
#         task_description: str,
#         output_types: str = "base,final,direct",
#         index: int = 0,
#         verbose: bool = True,
#         max_steps: int = 10,
#         max_time: int = 60,
#         output_json_dir: str = "results",
#         root_cache_dir: str = "cache"
#     ):
#         self.planner = planner
#         self.memory = memory
#         self.executor = executor
#         self.task = task
#         self.task_description = task_description
#         self.index = index
#         self.verbose = verbose
#         self.max_steps = max_steps
#         self.max_time = max_time
#         self.output_json_dir = output_json_dir
#         self.root_cache_dir = root_cache_dir

#         self.output_types = output_types.lower().split(',')
#         assert all(output_type in ["base", "final", "direct"] for output_type in self.output_types), "Invalid output type. Supported types are 'base', 'final', 'direct'."

#         # self.benchmark_data = self.load_benchmark_data()



#     def stream_solve_user_problem(self, user_query: str, user_image: Image.Image, messages: List[ChatMessage]) -> Iterator[List[ChatMessage]]:
#         """
#         Streams intermediate thoughts and final responses for the problem-solving process based on user input.
        
#         Args:
#             user_query (str): The text query input from the user.
#             user_image (Image.Image): The uploaded image from the user (PIL Image object).
#             messages (list): A list of ChatMessage objects to store the streamed responses.
#         """

#         if user_image:
#             # # Convert PIL Image to bytes (for processing)
#             # img_bytes_io = io.BytesIO()
#             # user_image.save(img_bytes_io, format="PNG")  # Convert image to PNG bytes
#             # img_bytes = img_bytes_io.getvalue()  # Get bytes
            
#             # Use image paths instead of bytes,
#             os.makedirs(os.path.join(self.root_cache_dir, 'images'), exist_ok=True)
#             img_path = os.path.join(self.root_cache_dir, 'images', str(uuid.uuid4()) + '.jpg')
#             user_image.save(img_path)
#         else:
#             img_path = None

#         # Set query cache
#         _cache_dir = os.path.join(self.root_cache_dir)
#         self.executor.set_query_cache_dir(_cache_dir)
        
#         # Step 1: Display the received inputs
#         if user_image:
#             messages.append(ChatMessage(role="assistant", content=f"📝 Received Query: {user_query}\n🖼️ Image Uploaded"))
#         else:
#             messages.append(ChatMessage(role="assistant", content=f"📝 Received Query: {user_query}"))
#         yield messages

#         # Step 2: Add "thinking" status while processing
#         messages.append(ChatMessage(
#             role="assistant",
#             content="",
#             metadata={"title": "⏳ Thinking: Processing input..."}
#         ))

#         # Step 3: Initialize problem-solving state
#         start_time = time.time()
#         step_count = 0
#         json_data = {"query": user_query, "image": "Image received as bytes"}

#         # Step 4: Query Analysis
#         import pdb; pdb.set_trace()
#         query_analysis = self.planner.analyze_query(user_query, img_path)
#         json_data["query_analysis"] = query_analysis
#         messages.append(ChatMessage(role="assistant", content=f"🔍 Query Analysis:\n{query_analysis}"))
#         yield messages

#         # Step 5: Execution loop (similar to your step-by-step solver)
#         while step_count < self.max_steps and (time.time() - start_time) < self.max_time:
#             step_count += 1
#             messages.append(ChatMessage(role="assistant", content=f"🔄 Step {step_count}: Generating next step..."))
#             yield messages

#             # Generate the next step
#             next_step = self.planner.generate_next_step(
#                 user_query, img_path, query_analysis, self.memory, step_count, self.max_steps
#             )
#             context, sub_goal, tool_name = self.planner.extract_context_subgoal_and_tool(next_step)

#             # Display the step information
#             messages.append(ChatMessage(
#                 role="assistant",
#                 content=f"📌 Step {step_count} Details:\n- Context: {context}\n- Sub-goal: {sub_goal}\n- Tool: {tool_name}"
#             ))
#             yield messages

#             # Handle tool execution or errors
#             if tool_name not in self.planner.available_tools:
#                 messages.append(ChatMessage(role="assistant", content=f"⚠️ Error: Tool '{tool_name}' is not available."))
#                 yield messages
#                 continue

#             # Execute the tool command
#             tool_command = self.executor.generate_tool_command(
#                 user_query, img_path, context, sub_goal, tool_name, self.planner.toolbox_metadata[tool_name]
#             )
#             explanation, command = self.executor.extract_explanation_and_command(tool_command)
#             result = self.executor.execute_tool_command(tool_name, command)
#             result = make_json_serializable(result)

#             messages.append(ChatMessage(role="assistant", content=f"✅ Step {step_count} Result:\n{json.dumps(result, indent=4)}"))
#             yield messages

#             # Step 6: Memory update and stopping condition
#             self.memory.add_action(step_count, tool_name, sub_goal, tool_command, result)
#             stop_verification = self.planner.verificate_memory(user_query, img_path, query_analysis, self.memory)
#             conclusion = self.planner.extract_conclusion(stop_verification)

#             messages.append(ChatMessage(role="assistant", content=f"🛑 Step {step_count} Conclusion: {conclusion}"))
#             yield messages

#             if conclusion == 'STOP':
#                 break

#         # Step 7: Generate Final Output (if needed)
#         if 'final' in self.output_types:
#             final_output = self.planner.generate_final_output(user_query, img_path, self.memory)
#             messages.append(ChatMessage(role="assistant", content=f"🎯 Final Output:\n{final_output}"))
#             yield messages

#         if 'direct' in self.output_types:
#             direct_output = self.planner.generate_direct_output(user_query, img_path, self.memory)
#             messages.append(ChatMessage(role="assistant", content=f"🔹 Direct Output:\n{direct_output}"))
#             yield messages

#         # Step 8: Completion Message
#         messages.append(ChatMessage(role="assistant", content="✅ Problem-solving process complete."))
#         yield messages
            
# def parse_arguments():
#     parser = argparse.ArgumentParser(description="Run the OpenTools demo with specified parameters.")
#     parser.add_argument("--llm_engine_name", default="gpt-4o", help="LLM engine name.")
#     parser.add_argument("--max_tokens", type=int, default=2000, help="Maximum tokens for LLM generation.")
#     parser.add_argument("--run_baseline_only", type=bool, default=False, help="Run only the baseline (no toolbox).")
#     parser.add_argument("--task", default="minitoolbench", help="Task to run.")
#     parser.add_argument("--task_description", default="", help="Task description.")
#     parser.add_argument(
#         "--output_types",
#         default="base,final,direct",
#         help="Comma-separated list of required outputs (base,final,direct)"
#     )
#     parser.add_argument("--enabled_tools", default="Generalist_Solution_Generator_Tool", help="List of enabled tools.")
#     parser.add_argument("--root_cache_dir", default="demo_solver_cache", help="Path to solver cache directory.")
#     parser.add_argument("--output_json_dir", default="demo_results", help="Path to output JSON directory.")
#     parser.add_argument("--max_steps", type=int, default=10, help="Maximum number of steps to execute.")
#     parser.add_argument("--max_time", type=int, default=60, help="Maximum time allowed in seconds.")
#     parser.add_argument("--verbose", type=bool, default=True, help="Enable verbose output.")
#     return parser.parse_args()


# def solve_problem_gradio(user_query, user_image):
#     """
#     Wrapper function to connect the solver to Gradio.
#     Streams responses from `solver.stream_solve_user_problem` for real-time UI updates.
#     """
#     global solver  # Ensure we're using the globally defined solver

#     if solver is None:
#         return [["assistant", "⚠️ Error: Solver is not initialized. Please restart the application."]]

#     messages = []  # Initialize message list
#     for message_batch in solver.stream_solve_user_problem(user_query, user_image, messages):
#         yield [[msg.role, msg.content] for msg in message_batch]  # Ensure correct format for Gradio Chatbot



# def main(args):
#     global solver
#     # Initialize Tools
#     enabled_tools = args.enabled_tools.split(",") if args.enabled_tools else []


#     # Instantiate Initializer
#     initializer = Initializer(
#         enabled_tools=enabled_tools,
#         model_string=args.llm_engine_name
#     )

#     # Instantiate Planner
#     planner = Planner(
#         llm_engine_name=args.llm_engine_name,
#         toolbox_metadata=initializer.toolbox_metadata,
#         available_tools=initializer.available_tools
#     )

#     # Instantiate Memory
#     memory = Memory()

#     # Instantiate Executor
#     executor = Executor(
#         llm_engine_name=args.llm_engine_name,
#         root_cache_dir=args.root_cache_dir,
#         enable_signal=False
#     )

#     # Instantiate Solver
#     solver = Solver(
#         planner=planner,
#         memory=memory,
#         executor=executor,
#         task=args.task,
#         task_description=args.task_description,
#         output_types=args.output_types,  # Add new parameter
#         verbose=args.verbose,
#         max_steps=args.max_steps,
#         max_time=args.max_time,
#         output_json_dir=args.output_json_dir,
#         root_cache_dir=args.root_cache_dir
#     )

#     # Test Inputs
#     # user_query = "How many balls are there in the image?"
#     # user_image_path = "/home/sheng/toolbox-agent/mathvista_113.png"  # Replace with your actual image path

#     # # Load the image as a PIL object
#     # user_image = Image.open(user_image_path).convert("RGB")  # Ensure it's in RGB mode

#     # print("\n=== Starting Problem Solving ===\n")
#     # messages = []
#     # for message_batch in solver.stream_solve_user_problem(user_query, user_image, messages):
#     #     for message in message_batch:
#     #         print(f"{message.role}: {message.content}") 

#     # messages = []
#     # solver.stream_solve_user_problem(user_query, user_image, messages)


#     # def solve_problem_stream(user_query, user_image):
#     #     messages = []  # Ensure it's a list of [role, content] pairs

#     #     for message_batch in solver.stream_solve_user_problem(user_query, user_image, messages):
#     #         yield message_batch  # Stream messages correctly in tuple format

#     # solve_problem_stream(user_query, user_image)

#     # ========== Gradio Interface ==========
#     with gr.Blocks() as demo:
#         gr.Markdown("# 🧠 OctoTools AI Solver")  # Title

#         with gr.Row():
#             user_query = gr.Textbox(label="Enter your query", placeholder="Type your question here...")
#             user_image = gr.Image(type="pil", label="Upload an image")  # Accepts multiple formats

#         run_button = gr.Button("Run")  # Run button
#         chatbot_output = gr.Chatbot(label="Problem-Solving Output")

#         # Link button click to function
#         run_button.click(fn=solve_problem_gradio, inputs=[user_query, user_image], outputs=chatbot_output)

#     # Launch the Gradio app
#     demo.launch()



# if __name__ == "__main__":
#     args = parse_arguments()
#     main(args)