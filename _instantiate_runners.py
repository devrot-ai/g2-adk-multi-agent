from google.adk.runners import InMemoryRunner, Runner
from google.adk.sessions import InMemorySessionService
from summarizer_agent.agent import root_agent

r1 = InMemoryRunner(agent=root_agent)
print('InMemoryRunner created:', type(r1).__name__, 'app_name=', r1.app_name)

r2 = Runner(app_name='summarizer_agent', agent=root_agent, session_service=InMemorySessionService(), auto_create_session=True)
print('Runner created:', type(r2).__name__, 'app_name=', r2.app_name, 'auto_create_session=', r2.auto_create_session)
