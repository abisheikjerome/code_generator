import os
import boto3
from langchain_aws import ChatBedrock

#SQ 1.18 - 1.21 it handles the invokcation of the bedrock client 

class ClientUtility:
    def get_bedrock_client(self):
        client = boto3.client(
            service_name="bedrock-runtime",
            region_name=os.getenv("REGION"),
            aws_access_key_id =os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        )       
        return client
    def get_llm(self,max_tokens=500, temperature=0.2):
        llm = ChatBedrock(
            client=self.get_bedrock_client(),
            model_id=os.getenv("MODEL_ID"),
            provider="amazon",
            model_kwargs={
                "maxTokenCount": max_tokens,
                "temperature": temperature,
            },
        )   
        return llm