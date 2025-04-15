from pydantic import BaseModel, Field
from typing import List, Optional
from openai import OpenAI
from openai import AzureOpenAI
import os
import csv
import utils
import json


# Access environment variables
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
openai_api_key = os.getenv("AZURE_OPEN_AI_API_KEY")
azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
azure_openai_model = os.getenv("AZURE_OPENAI_DEPLOYMENT")

class ResumeChecklist(BaseModel):
    skills: List[str] = Field(..., description="Technical or professional skills listed")
    experience_years: int = Field(..., description="Total number of years of professional experience")
    education_level: str = Field(..., description="Highest education level attained (e.g. Bachelor's, Master's, PhD, BS, BE, Btech, MS, MBA)")
    last_job_role: str = Field(..., description="Most recent or current job title mentioned in resume")
    salary_expectation: Optional[int] = Field(None, description="Salary expectation if explicitly mentioned (annual, USD)")
    projects_count: Optional[int] = Field(None, description="Number of distinct projects mentioned or led in resume")

def extract_features(resumesummary):
    try:
        features=[]
        client = AzureOpenAI(
        azure_endpoint=azure_endpoint,
        api_key=openai_api_key,
        api_version=azure_openai_api_version
        )
        for resume_text in resumesummary:
            response = client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": "Extract structured details from the resume provided by the user."},
                    {"role": "user", "content": resume_text}
                ],
                response_format=ResumeChecklist
            )
            resume_data = response.choices[0].message.content           
            features.append(resume_data)
        
        return features
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def evalagainstchecklist(file_path,resumedata):
    try:
        count= len(resumedata)
        manualchecklist= utils.extract_all_manualchecklistintolist(file_path)
        for i in range(count):
            row= manualchecklist[i]
            resumesummarytxt=resumedata[i]
            resumesummary = json.loads(resumesummarytxt)
            skills_from_checklist = row[0].split(",") if row[0] else []
            experience_yearsfromchecklist= row[1]
            education_levelfromchecklist = row[2]
            last_job_rolefromchecklist= row[3]
            salary_expectationfromchecklist= row[4]
            projects_countfromchecklist= row[5]                   
            similarity=utils.percentagesimilaritysummaryssameaschecklist(resumesummary.get("skills",[]),skills_from_checklist)
            smexp = utils.percentagesimilaritysummaryssameaschecklistINT(int(resumesummary.get("experience_years", 0)), int(experience_yearsfromchecklist))
            smeduc= utils.percentagesimilaritysummaryssameaschecklistSTR(resumesummary.get("education_level"),education_levelfromchecklist)
            smjob= utils.percentagesimilaritysummaryssameaschecklistSTR(resumesummary.get("last_job_role"),last_job_rolefromchecklist)
            if salary_expectationfromchecklist != "N/A":
                smsalary= utils.percentagesimilaritysummaryssameaschecklistINT(resumesummary.get("salary_expectation"),salary_expectationfromchecklist)
            else:
                if salary_expectationfromchecklist == "N/A" or resumesummary.get("salary_expectation") == "N/A" or resumesummary.get("salary_expectation") == None:
                    smsalary = 100
                else:
                    smsalary = 0
            smprojects= utils.percentagesimilaritysummaryssameaschecklistINT(resumesummary.get("projects_count"), int(projects_countfromchecklist))
            if similarity==100 and smexp== 100 and smeduc == 100 and smjob == 100 and smsalary == 100 and smprojects == 100:
                print("OpenAI resume summary",resumesummary)
                print("Manual checklist",row)
                print("Resume matches the checklist")
                            
            else:
                print("OpenAI resume summary",resumesummary)
                print("Manual checklist",row)
                print("Skills similarity: ", similarity)
                print("Experience years similarity: ", smexp)
                print("Education level similarity: ", smeduc)
                print("Last job role similarity: ", smjob)
                print("Salary expectation similarity: ", smsalary)
                print("Projects count similarity: ", smprojects)
       
    
    except Exception as e:
        print(f"Error reading CSV file: {e}")
def main():
    resumesummary= utils.getsummaryfromresumedatacsv()
    
    features=extract_features(resumesummary)
 
    evalagainstchecklist("resume/resumechecklist.csv",features)
    

if __name__ == "__main__":
    main()