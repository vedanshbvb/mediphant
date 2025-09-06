# import sys
# import os
# import glob
# import asyncio
# from google.adk.sessions import InMemorySessionService
# from google.adk.runners import Runner
# from google.genai import types
# from agents.root_agent import RootAgent

# def get_project_root():
#     # Returns the medical_agent/ directory (one level up from this file)
#     return os.path.dirname(os.path.abspath(__file__))

# LOG_FILE = os.path.join(get_project_root(), "run_pipeline.log")

# def log_line(line):
#     with open(LOG_FILE, "a") as f:
#         f.write(line + "\n")

def get_greeting():
    return "Hello! How can I assist you with your medical appointment today?"

# async def main():
#     if len(sys.argv) < 2:
#         log_line("STATUS: No prompt provided.")
#         print("Usage: python run_pipeline.py '<user_prompt>'")
#         sys.exit(1)
    
#     user_prompt = sys.argv[1]
#     app_name = "medical_pipeline"
#     user_id = "user1"
#     session_id = "session1"

#     session_service = InMemorySessionService()
#     await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)

#     runner = Runner(agent=RootAgent, app_name=app_name, session_service=session_service)

#     try:
#         content = types.Content(role='user', parts=[types.Part(text=user_prompt)])
#         events = runner.run(user_id=user_id, session_id=session_id, new_message=content)
        
#         for event in events:
#             log_line(f"EVENT: {type(event).__name__}")
#             if hasattr(event, 'content') and event.content:
#                 if hasattr(event.content, 'parts') and event.content.parts:
#                     log_line(f"CONTENT: {event.content.parts[0].text}")
        
#         log_line("STATUS: RootAgent completed successfully.")
#         print(f"[SUCCESS] Pipeline completed. Check {LOG_FILE} for detailed logs.")
        
#     except Exception as e:
#         error_msg = f"STATUS: Error running pipeline: {str(e)}"
#         log_line(error_msg)
#         print(f"[ERROR] {error_msg}")
#         sys.exit(1)





