import json
from openai import OpenAI
from .patient_rag import PatientRAG
from typing import Dict, List, Optional, Any

class LLM:
    def __init__(self, api_key):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.asi1.ai/v1"
        )

    def create_completion(self, prompt, max_tokens=200):
        completion = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="asi1-mini",
            max_tokens=max_tokens
        )
        return completion.choices[0].message.content

def get_medical_intent_and_keyword(query, llm):
    """Use LLM to classify medical intent and extract keywords."""
    prompt = (
        f"Given the medical query: '{query}'\n"
        "Classify the intent as one of: 'symptom_assessment', 'medication_info', 'appointment_scheduling', 'preventive_care', 'lab_results', 'specialist_referral', 'emergency_check', 'treatment_advice', 'faq', or 'unknown'.\n"
        "Extract the most relevant medical keywords (e.g., fever, headache, medication names, body parts, symptoms) from the query.\n"
        "Return *only* the result in JSON format like this, with no additional text:\n"
        "{\n"
        "  \"intent\": \"<classified_intent>\",\n"
        "  \"keywords\": [\"<keyword1>\", \"<keyword2>\", \"<keyword3>\"]\n"
        "}"
    )
    response = llm.create_completion(prompt)
    try:
        result = json.loads(response)
        return result["intent"], result["keywords"]
    except json.JSONDecodeError:
        print(f"Error parsing LLM response: {response}")
        return "unknown", []

def generate_medical_knowledge_response(query, intent, keywords, llm):
    """Use LLM to generate medical responses based on intent."""
    if intent == "symptom_assessment":
        prompt = (
            f"Query: '{query}'\n"
            f"Symptoms mentioned: {', '.join(keywords)}\n"
            "Provide a professional medical assessment guide for these symptoms. Include when to seek medical care.\n"
            "Return *only* the medical guidance, no additional text."
        )
    elif intent == "medication_info":
        prompt = (
            f"Query: '{query}'\n"
            f"Medication mentioned: {', '.join(keywords)}\n"
            "Provide general information about this medication including common uses and precautions.\n"
            "Return *only* the medication information, no additional text."
        )
    elif intent == "preventive_care":
        prompt = (
            f"Query: '{query}'\n"
            f"Keywords: {', '.join(keywords)}\n"
            "Provide preventive care recommendations and screening guidelines.\n"
            "Return *only* the preventive care advice, no additional text."
        )
    elif intent == "emergency_check":
        prompt = (
            f"Query: '{query}'\n"
            f"Concerning symptoms: {', '.join(keywords)}\n"
            "Assess if these symptoms require emergency care. Provide clear guidance on urgency level.\n"
            "Return *only* the emergency assessment, no additional text."
        )
    elif intent == "treatment_advice":
        prompt = (
            f"Query: '{query}'\n"
            f"Condition/symptoms: {', '.join(keywords)}\n"
            "Provide general treatment advice and home care recommendations.\n"
            "Return *only* the treatment guidance, no additional text."
        )
    elif intent == "faq":
        prompt = (
            f"Query: '{query}'\n"
            "This is a general medical question. Provide a helpful, accurate answer with appropriate medical disclaimers.\n"
            "Return *only* the answer, no additional text."
        )
    else:
        return None
    return llm.create_completion(prompt, max_tokens=300)

def process_medical_query(query, rag: PatientRAG, llm: LLM, patient_context: Optional[Dict] = None):
    """Process medical queries using the patient knowledge graph and LLM."""
    intent, keywords = get_medical_intent_and_keyword(query, llm)
    print(f"Medical Intent: {intent}, Keywords: {keywords}")
    
    response_data = {
        "query": query,
        "intent": intent,
        "keywords": keywords,
        "knowledge_graph_results": {},
        "recommendations": {},
        "urgency_level": "unknown"
    }
    
    if intent == "symptom_assessment" and keywords:
        # Use knowledge graph for symptom analysis
        symptom_analysis = rag.query_symptoms_conditions(keywords)
        urgency_assessment = rag.assess_urgency_level(keywords, patient_context)
        
        response_data["knowledge_graph_results"] = symptom_analysis
        response_data["urgency_assessment"] = urgency_assessment
        response_data["urgency_level"] = urgency_assessment.get("urgency_level", "unknown")
        
        # Get specialist recommendations
        conditions = [item['condition'] for item in symptom_analysis]
        specialists = rag.get_specialist_recommendation(conditions)
        response_data["specialist_recommendations"] = specialists
        
        # Generate comprehensive response
        prompt = (
            f"Medical Query: '{query}'\n"
            f"Symptoms Analyzed: {keywords}\n"
            f"Knowledge Graph Analysis: {symptom_analysis}\n"
            f"Urgency Level: {urgency_assessment.get('urgency_level', 'unknown')}\n"
            f"Recommended Specialists: {specialists}\n"
            "Provide a comprehensive medical response including symptom assessment, urgency guidance, and next steps.\n"
            "Include appropriate medical disclaimers."
        )
        
    elif intent == "medication_info" and keywords:
        # Use knowledge graph for medication information
        medication_info = {}
        for med in keywords:
            med_data = rag.get_medication_info(med)
            if med_data['dosage'] or med_data['contraindications']:
                medication_info[med] = med_data
        
        response_data["knowledge_graph_results"] = medication_info
        
        # Check for drug interactions if multiple medications
        if len(keywords) > 1:
            safety_report = rag.check_medication_safety(keywords, 
                patient_context.get('age_group', 'adult') if patient_context else 'adult')
            response_data["medication_safety"] = safety_report
        
        prompt = (
            f"Medication Query: '{query}'\n"
            f"Medications: {keywords}\n"
            f"Knowledge Graph Information: {medication_info}\n"
            "Provide comprehensive medication information including dosages, contraindications, and safety considerations.\n"
            "Include appropriate medical disclaimers about consulting healthcare providers."
        )
        
    elif intent == "preventive_care" and patient_context:
        age_group = patient_context.get('age_group')
        if age_group:
            preventive_care = rag.get_preventive_care_recommendations(age_group)
            response_data["knowledge_graph_results"] = {
                "age_group": age_group,
                "recommendations": preventive_care
            }
            
            prompt = (
                f"Preventive Care Query: '{query}'\n"
                f"Patient Age Group: {age_group}\n"
                f"Recommendations: {preventive_care}\n"
                "Provide comprehensive preventive care guidance for this age group.\n"
                "Include appropriate medical disclaimers."
            )
        else:
            prompt = f"Query: '{query}'\nProvide general preventive care recommendations across different age groups."
            
    elif intent == "emergency_check" and keywords:
        # Check for warning signs
        warning_actions = {}
        for keyword in keywords:
            action = rag.get_warning_signs_action(keyword)
            if action != "Consult healthcare provider":  # Only store specific actions
                warning_actions[keyword] = action
        
        response_data["warning_signs"] = warning_actions
        
        # Assess overall urgency
        urgency_assessment = rag.assess_urgency_level(keywords, patient_context)
        response_data["urgency_assessment"] = urgency_assessment
        response_data["urgency_level"] = urgency_assessment.get("urgency_level", "unknown")
        
        prompt = (
            f"Emergency Assessment Query: '{query}'\n"
            f"Symptoms/Signs: {keywords}\n"
            f"Warning Sign Actions: {warning_actions}\n"
            f"Urgency Assessment: {urgency_assessment}\n"
            "Provide immediate emergency assessment and clear guidance on what action to take.\n"
            "Be specific about when to call 911, go to ER, or schedule urgent care."
        )
        
    elif intent == "faq":
        # Check knowledge graph for FAQ
        faq_answer = rag.query_faq(query)
        if faq_answer:
            response_data["knowledge_graph_results"] = {"faq_answer": faq_answer}
            prompt = (
                f"FAQ Query: '{query}'\n"
                f"Knowledge Base Answer: '{faq_answer}'\n"
                "Expand on this answer with additional helpful medical guidance and appropriate disclaimers."
            )
        else:
            # Generate new FAQ response
            new_answer = generate_medical_knowledge_response(query, intent, keywords, llm)
            if new_answer:
                rag.add_patient_knowledge("faq", query, new_answer)
                response_data["knowledge_graph_results"] = {"generated_answer": new_answer}
                prompt = (
                    f"FAQ Query: '{query}'\n"
                    f"Generated Answer: '{new_answer}'\n"
                    "Provide this as professional medical guidance with appropriate disclaimers."
                )
            else:
                prompt = f"Medical Question: '{query}'\nProvide a helpful medical response with appropriate disclaimers."
    
    elif intent == "appointment_scheduling":
        # Get appointment duration recommendations
        appointment_type = "consultation"  # default
        for keyword in keywords:
            if keyword in ["checkup", "physical", "exam"]:
                appointment_type = "routine_checkup"
            elif keyword in ["follow", "followup"]:
                appointment_type = "follow_up"
        
        duration = rag.get_appointment_duration_recommendation(appointment_type)
        response_data["appointment_recommendation"] = {
            "type": appointment_type,
            "duration": duration
        }
        
        prompt = (
            f"Appointment Query: '{query}'\n"
            f"Recommended Type: {appointment_type}\n"
            f"Recommended Duration: {duration}\n"
            "Provide guidance on appointment scheduling and what to expect.\n"
            "Include preparation tips for the appointment."
        )
    
    else:
        # Default response for unknown intents
        prompt = f"Medical Query: '{query}'\nProvide helpful medical information with appropriate disclaimers about consulting healthcare professionals."
    
    # Generate final response using LLM
    llm_response = llm.create_completion(prompt, max_tokens=400)
    
    response_data["final_response"] = llm_response
    response_data["medical_disclaimer"] = "This information is for educational purposes only. Always consult with a qualified healthcare professional for medical advice, diagnosis, or treatment."
    
    return response_data

def format_comprehensive_medical_response(response_data: Dict) -> str:
    """Format the comprehensive medical response for display."""
    query = response_data.get("query", "")
    intent = response_data.get("intent", "unknown")
    urgency_level = response_data.get("urgency_level", "unknown")
    final_response = response_data.get("final_response", "")
    
    # Urgency indicator
    urgency_emojis = {
        "emergency": "🚨 EMERGENCY",
        "urgent": "⚠️ URGENT", 
        "moderate": "📋 MODERATE",
        "routine": "📅 ROUTINE",
        "unknown": "ℹ️ ASSESSMENT"
    }
    
    urgency_indicator = urgency_emojis.get(urgency_level, "ℹ️ ASSESSMENT")
    
    formatted_response = f"""🏥 **Medical Assistant Response**

**{urgency_indicator}** | Query: "{query}"

{final_response}

"""
    
    # Add specific knowledge graph insights
    if intent == "symptom_assessment":
        kg_results = response_data.get("knowledge_graph_results", [])
        if kg_results:
            formatted_response += "**📊 Symptom Analysis:**\n"
            for item in kg_results:
                formatted_response += f"• {item['symptom'].replace('_', ' ').title()}: {item['condition'].replace('_', ' ').title()}\n"
                if item.get('urgency') != 'unknown':
                    formatted_response += f"  - Urgency: {item['urgency'].title()}\n"
            formatted_response += "\n"
        
        specialists = response_data.get("specialist_recommendations", {})
        if specialists:
            formatted_response += "**👨‍⚕️ Specialist Recommendations:**\n"
            for specialty, conditions in specialists.items():
                formatted_response += f"• {specialty.replace('_', ' ').title()}: {', '.join(conditions)}\n"
            formatted_response += "\n"
    
    elif intent == "medication_info":
        med_safety = response_data.get("medication_safety", {})
        if med_safety.get("interactions"):
            formatted_response += "**⚠️ Drug Interaction Warnings:**\n"
            for interaction in med_safety["interactions"]:
                formatted_response += f"• {interaction['drug1']} + {interaction['drug2']}: {interaction['risk']}\n"
            formatted_response += "\n"
    
    # Add disclaimer
    formatted_response += f"""**⚠️ Medical Disclaimer:**
{response_data.get('medical_disclaimer', '')}

**📞 Emergency:** For urgent medical concerns, call emergency services or visit the nearest emergency room."""
    
    return formatted_response

def get_patient_specific_insights(patient_data: Dict, rag: PatientRAG) -> Dict:
    """Generate patient-specific insights using the knowledge graph."""
    insights = {
        "patient_id": patient_data.get("patient_id"),
        "risk_assessment": {},
        "personalized_recommendations": [],
        "preventive_care": {},
        "medication_review": {}
    }
    
    # Comprehensive patient assessment
    if patient_data:
        assessment = rag.comprehensive_patient_assessment(patient_data)
        insights.update(assessment)
    
    # Get personalized recommendations if patient has symptom history
    patient_id = patient_data.get("patient_id")
    current_symptoms = patient_data.get("current_symptoms", [])
    if patient_id and current_symptoms:
        personalized_recs = rag.get_personalized_recommendations(patient_id, current_symptoms)
        insights["personalized_recommendations"] = personalized_recs
    
    # Risk assessment
    risk_assessment = rag.get_patient_risk_assessment(patient_data)
    insights["risk_assessment"] = risk_assessment
    
    return insights

def enhance_appointment_with_knowledge_graph(appointment_data: Dict, rag: PatientRAG, llm: LLM) -> Dict:
    """Enhance appointment data with knowledge graph insights."""
    enhanced_data = appointment_data.copy()
    
    # Analyze appointment notes for symptoms
    notes = appointment_data.get("notes", "")
    if notes:
        intent, keywords = get_medical_intent_and_keyword(notes, llm)
        if intent == "symptom_assessment" and keywords:
            symptom_analysis = rag.query_symptoms_conditions(keywords)
            urgency_assessment = rag.assess_urgency_level(keywords)
            
            enhanced_data["knowledge_graph_analysis"] = {
                "symptoms_detected": keywords,
                "possible_conditions": symptom_analysis,
                "urgency_assessment": urgency_assessment
            }
            
            # Recommend appropriate appointment duration
            if urgency_assessment.get("urgency_level") in ["emergency", "urgent"]:
                enhanced_data["recommended_duration"] = "60 minutes (extended for urgent assessment)"
            else:
                enhanced_data["recommended_duration"] = rag.get_appointment_duration_recommendation("consultation")
    
    return enhanced_data