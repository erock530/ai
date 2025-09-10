import openai
import anthropic
import google.generativeai as genai

from dotenv import load_dotenv
import os
import json
import warnings
# suppress warnings
warnings.filterwarnings("ignore")

class Agent:
    def __init__(self, model_name, system_prompt, provider, response_format='text'):
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.provider = provider.lower()
        self.response_format = response_format
        self.client = self._load_client()
    
    def _load_client(self):
        if self.provider == 'openai':
            # check if environment variable OPENAI_API_KEY is set
            if 'OPENAI_API_KEY' not in os.environ:
                load_dotenv()
            OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            return client
        elif self.provider == 'anthropic':
            if 'ANTHROPIC_API_KEY' not in os.environ:
                load_dotenv()
            ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            return client
        elif self.provider == 'google':
            if 'GEMINI_API_KEY' not in os.environ:
                load_dotenv()
            GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
            genai.configure(api_key=GEMINI_API_KEY)
            client = genai.GenerativeModel(self.model_name,
                system_instruction=self.system_prompt)
            return client
        elif self.provider == 'meta':
            # return MetaClient()
            raise NotImplementedError("Meta API not implemented yet")
        elif self.provider == 'x':
            # return XClient()
            raise NotImplementedError("X API not implemented yet")
        else:
            raise ValueError("Unsupported provider")
    
    def __call__(self, messages=[]):
        if self.provider == 'openai':
            return self.call_openai(messages)
        elif self.provider == 'anthropic':
            return self.call_anthropic(messages)
        elif self.provider == 'google':
            return self.call_google(messages)
        elif self.provider == 'meta':
            return self.call_meta(messages)
        elif self.provider == 'x':
            return self.call_x(messages)
        else:
            raise ValueError("Unsupported provider")

    @staticmethod
    def _parse_messages_athropic(messages):
        # messages have to alternate between user and assistant. However this is not always the case in the input. Join not alternating messages with "\n\n".
        alternating_messages = []
        last_role = None
        for message in messages:
            if last_role == None:
                if message["role"] == "user":
                    alternating_messages.append(message)
                    last_role = "user"
                continue
            if message["role"] != last_role:
                alternating_messages.append(message)
                last_role = message["role"]
            else:
                alternating_messages[-1]["content"] += "\n\n" + message["content"]
        return alternating_messages

    @staticmethod
    def post_process(response):
        # replace '**' with single '*' for bold formatting
        response = response.replace('**', '*')
        return response

    
    def call_openai(self, messages):
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "system", "content": self.system_prompt}]+messages[-10:],
            response_format={"type": self.response_format}
        )
        return self.post_process(response.choices[0].message.content)

    def call_anthropic(self, messages):
        messages = [{"role": message["role"], "content": [{"type": "text","text":message["content"]}]} for message in messages]
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=1000,
            temperature=0.8,
            system=self.system_prompt,
            messages=self._parse_messages_athropic(messages[-10:]),
            # response_format=NOT SUPPORTED
        )
        return response.content[0].text

    def call_google(self, messages):
        messages = [{"role": "model" if message["role"] == "assistant" else "user", "parts": message["content"]} for message in messages]
        chat = self.client.start_chat(
            history=messages[-10:-1],
        )
        response = chat.send_message(messages[-1]["parts"])
        return self.post_process(response.text)
    
    def call_meta(self, messages):
        # Meta API call logic here
        response = "Meta response based on " + self.model_name
        return response

    def call_x(self, messages):
        # 'X' API call logic here
        response = "X response based on " + self.model_name
        return response
    
class ResponseConstructor:
    def __init__(self):
        self.agents = self.load_agents()
        
    def load_agents(self):
        agent_prompts = json.load(open(os.path.join(os.getcwd(),'agent_logic','agent_prompts_extended.json')))
        agents = {}
        for agent_name, agent_prompt in agent_prompts.items():
            agents[agent_name] = Agent(model_name=agent_prompt["model_name"],
                                        system_prompt=agent_prompt["prompt"],
                                        provider=agent_prompt["api_provider"],
                                        response_format=agent_prompt["response_format"])
        return agents
    
    def __call__(self, messages, post_thread, verbose=False):
        thread_messages = []
        timestamps = []
        
        # call judge agent and check if the user question is simple
        judge_response = self.agents["Judge"](messages)
        post_thread('Judge',judge_response, thread_messages, timestamps)
        if verbose:
            print(f'<User>\n{messages[-1]["content"]}\n</User>')
            print(f'<Judge>\n{judge_response}\n</Judge>')
        if judge_response.split(':')[-1][:2] in ["tr","Tr","'t","'T",'"t','"T',' t',' T']:
            # call general agent
            if verbose:
                print("User question is simple")
            response = self.agents["General Agent"](messages)
        else:
            if verbose:
                print("User question is complex")
            # callect responses from Research Scientist, Psychologist, Career Advisor, Friend, Information Retriever
            responses = {}
            for agent_name in ["Research Scientist", "Psychologist", "Career Advisor", "Friend", "Information Retriever"]:
                # debbuging message
                if verbose:
                    print(f'Calling <{agent_name}>')
                responses[agent_name] = self.agents[agent_name](messages)
                post_thread(f"{agent_name} ({self.agents[agent_name].model_name})", responses[agent_name], thread_messages, timestamps)
            responses_concise_format = '\n'.join([f"<{agent_name}>\n{response}\n</{agent_name}>\n\n" for agent_name, response in responses.items()])
            if verbose:
                print(responses_concise_format)
            # get messeges and responses in concise format and give it to summarizer agent
            messages_responses = messages + [{"role": "system", "content": f'These are responses of several different experts:\n{responses_concise_format}\n\n Use this information to gain more insights but remember - the person you are speaking with do not have access to these responses - you have to formulate the answer to the original question in your own words.'}]
            response = self.agents["Summarizer"](messages_responses)
        return response, thread_messages, timestamps


# testing the agents
def _openai_test():
    openai_agent = Agent(model_name="gpt-3.5-turbo",
                         system_prompt="You are a helpful assistant that provides information and answers questions. You can also provide explanations and summaries.",
                         provider="openai")
    response = openai_agent([{"role": "user", "content": "What is the capital of France?"}])
    print(f"OpenAI response: {response}")
    
def _anthropic_test():
    anthropic_agent = Agent(model_name="claude-3-5-sonnet-20240620",
                            system_prompt="You are a helpful assistant that provides information and answers questions. You can also provide explanations and summaries.",
                            provider="anthropic")
    response = anthropic_agent([{"role": "user", "content": "What is the capital of France?"}])
    print(f"Anthropic response: {response}")

def _google_test():
    google_agent = Agent(model_name="gemini-1.5-flash",
                         system_prompt="You are a helpful assistant that provides information and answers questions. You can also provide explanations and summaries.",
                         provider="google")
    response = google_agent([{"role": "user", "content": "What is the capital of France?"}])
    print(f"Google response: {response}")

if __name__ == '__main__':
    try:
        _openai_test()
    except Exception as e:
        print(f"OpenAI test failed: {e}")
    try:
        _anthropic_test()
    except Exception as e:
        print(f"Anthropic test failed: {e}")
    try:
        _google_test()
    except Exception as e:
        print(f"Google test failed: {e}")