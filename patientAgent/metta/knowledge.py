from hyperon import MeTTa, E, S, ValueAtom

def initialize_patient_knowledge(metta: MeTTa):
    """Initialize the MeTTa knowledge graph with patient care, medical, and health data."""
    
    # Symptom → Possible Conditions
    metta.space().add_atom(E(S("symptom_condition"), S("fever"), S("viral_infection")))
    metta.space().add_atom(E(S("symptom_condition"), S("fever"), S("bacterial_infection")))
    metta.space().add_atom(E(S("symptom_condition"), S("fever"), S("flu")))
    metta.space().add_atom(E(S("symptom_condition"), S("headache"), S("tension_headache")))
    metta.space().add_atom(E(S("symptom_condition"), S("headache"), S("migraine")))
    metta.space().add_atom(E(S("symptom_condition"), S("headache"), S("sinus_infection")))
    metta.space().add_atom(E(S("symptom_condition"), S("cough"), S("common_cold")))
    metta.space().add_atom(E(S("symptom_condition"), S("cough"), S("bronchitis")))
    metta.space().add_atom(E(S("symptom_condition"), S("cough"), S("pneumonia")))
    metta.space().add_atom(E(S("symptom_condition"), S("chest_pain"), S("heart_condition")))
    metta.space().add_atom(E(S("symptom_condition"), S("chest_pain"), S("muscle_strain")))
    metta.space().add_atom(E(S("symptom_condition"), S("nausea"), S("stomach_bug")))
    metta.space().add_atom(E(S("symptom_condition"), S("nausea"), S("food_poisoning")))
    
    # Condition → Urgency Level
    metta.space().add_atom(E(S("urgency_level"), S("heart_condition"), ValueAtom("emergency")))
    metta.space().add_atom(E(S("urgency_level"), S("chest_pain"), ValueAtom("urgent")))
    metta.space().add_atom(E(S("urgency_level"), S("pneumonia"), ValueAtom("urgent")))
    metta.space().add_atom(E(S("urgency_level"), S("high_fever"), ValueAtom("urgent")))
    metta.space().add_atom(E(S("urgency_level"), S("common_cold"), ValueAtom("routine")))
    metta.space().add_atom(E(S("urgency_level"), S("tension_headache"), ValueAtom("routine")))
    metta.space().add_atom(E(S("urgency_level"), S("migraine"), ValueAtom("moderate")))
    metta.space().add_atom(E(S("urgency_level"), S("bronchitis"), ValueAtom("moderate")))
    metta.space().add_atom(E(S("urgency_level"), S("stomach_bug"), ValueAtom("routine")))
    
    # Condition → Treatment Recommendations
    metta.space().add_atom(E(S("treatment"), S("viral_infection"), ValueAtom("rest, fluids, monitor temperature")))
    metta.space().add_atom(E(S("treatment"), S("bacterial_infection"), ValueAtom("antibiotics, rest, follow-up")))
    metta.space().add_atom(E(S("treatment"), S("common_cold"), ValueAtom("rest, warm fluids, honey for cough")))
    metta.space().add_atom(E(S("treatment"), S("tension_headache"), ValueAtom("rest, hydration, gentle massage")))
    metta.space().add_atom(E(S("treatment"), S("migraine"), ValueAtom("dark room, cold compress, prescribed medication")))
    metta.space().add_atom(E(S("treatment"), S("bronchitis"), ValueAtom("rest, warm humidified air, cough suppressants")))
    metta.space().add_atom(E(S("treatment"), S("pneumonia"), ValueAtom("antibiotics, rest, monitor breathing")))
    metta.space().add_atom(E(S("treatment"), S("stomach_bug"), ValueAtom("clear fluids, BRAT diet, electrolytes")))
    
    # Medication → Dosage Information
    metta.space().add_atom(E(S("medication_dosage"), S("acetaminophen"), ValueAtom("500-1000mg every 6-8 hours, max 3000mg/day")))
    metta.space().add_atom(E(S("medication_dosage"), S("ibuprofen"), ValueAtom("400-600mg every 6-8 hours, max 2400mg/day")))
    metta.space().add_atom(E(S("medication_dosage"), S("amoxicillin"), ValueAtom("500mg every 8 hours for 7-10 days")))
    metta.space().add_atom(E(S("medication_dosage"), S("azithromycin"), ValueAtom("500mg day 1, then 250mg daily for 4 days")))
    metta.space().add_atom(E(S("medication_dosage"), S("dextromethorphan"), ValueAtom("15-30mg every 4 hours, max 120mg/day")))
    
    # Medication → Contraindications
    metta.space().add_atom(E(S("contraindication"), S("aspirin"), ValueAtom("children under 16, bleeding disorders")))
    metta.space().add_atom(E(S("contraindication"), S("ibuprofen"), ValueAtom("kidney disease, heart failure, stomach ulcers")))
    metta.space().add_atom(E(S("contraindication"), S("amoxicillin"), ValueAtom("penicillin allergy")))
    metta.space().add_atom(E(S("contraindication"), S("codeine"), ValueAtom("pregnancy, respiratory depression")))
    
    # Age Group → Medication Safety
    metta.space().add_atom(E(S("age_safe_medication"), S("pediatric"), S("acetaminophen")))
    metta.space().add_atom(E(S("age_safe_medication"), S("pediatric"), S("ibuprofen")))
    metta.space().add_atom(E(S("age_safe_medication"), S("elderly"), S("acetaminophen")))
    metta.space().add_atom(E(S("age_safe_medication"), S("adult"), S("ibuprofen")))
    metta.space().add_atom(E(S("age_safe_medication"), S("adult"), S("aspirin")))
    
    # Specialty → Common Conditions
    metta.space().add_atom(E(S("specialty_condition"), S("cardiology"), S("hypertension")))
    metta.space().add_atom(E(S("specialty_condition"), S("cardiology"), S("heart_disease")))
    metta.space().add_atom(E(S("specialty_condition"), S("pulmonology"), S("asthma")))
    metta.space().add_atom(E(S("specialty_condition"), S("pulmonology"), S("bronchitis")))
    metta.space().add_atom(E(S("specialty_condition"), S("neurology"), S("migraine")))
    metta.space().add_atom(E(S("specialty_condition"), S("neurology"), S("seizures")))
    metta.space().add_atom(E(S("specialty_condition"), S("gastroenterology"), S("acid_reflux")))
    metta.space().add_atom(E(S("specialty_condition"), S("gastroenterology"), S("ibs")))
    metta.space().add_atom(E(S("specialty_condition"), S("dermatology"), S("eczema")))
    metta.space().add_atom(E(S("specialty_condition"), S("dermatology"), S("acne")))
    
    # Appointment Type → Duration
    metta.space().add_atom(E(S("appointment_duration"), S("routine_checkup"), ValueAtom("30 minutes")))
    metta.space().add_atom(E(S("appointment_duration"), S("follow_up"), ValueAtom("15 minutes")))
    metta.space().add_atom(E(S("appointment_duration"), S("consultation"), ValueAtom("45 minutes")))
    metta.space().add_atom(E(S("appointment_duration"), S("physical_exam"), ValueAtom("60 minutes")))
    metta.space().add_atom(E(S("appointment_duration"), S("specialist_consultation"), ValueAtom("60 minutes")))
    
    # Preventive Care → Age Guidelines
    metta.space().add_atom(E(S("preventive_care"), S("20s"), ValueAtom("annual checkup, vaccinations, STD screening")))
    metta.space().add_atom(E(S("preventive_care"), S("30s"), ValueAtom("blood pressure, cholesterol, diabetes screening")))
    metta.space().add_atom(E(S("preventive_care"), S("40s"), ValueAtom("mammogram, colonoscopy prep, heart health")))
    metta.space().add_atom(E(S("preventive_care"), S("50s"), ValueAtom("colonoscopy, bone density, cancer screening")))
    metta.space().add_atom(E(S("preventive_care"), S("60s"), ValueAtom("comprehensive screening, vision, hearing")))
    
    # Lab Test → Normal Ranges
    metta.space().add_atom(E(S("lab_normal_range"), S("blood_glucose"), ValueAtom("70-100 mg/dL fasting")))
    metta.space().add_atom(E(S("lab_normal_range"), S("cholesterol_total"), ValueAtom("less than 200 mg/dL")))
    metta.space().add_atom(E(S("lab_normal_range"), S("blood_pressure"), ValueAtom("120/80 mmHg or lower")))
    metta.space().add_atom(E(S("lab_normal_range"), S("hemoglobin"), ValueAtom("12-15.5 g/dL women, 13.5-17.5 g/dL men")))
    metta.space().add_atom(E(S("lab_normal_range"), S("white_blood_cells"), ValueAtom("4,500-11,000 cells/mcL")))
    
    # Warning Signs → Immediate Action
    metta.space().add_atom(E(S("warning_sign"), S("chest_pain_crushing"), ValueAtom("call 911 immediately")))
    metta.space().add_atom(E(S("warning_sign"), S("difficulty_breathing"), ValueAtom("seek emergency care")))
    metta.space().add_atom(E(S("warning_sign"), S("severe_headache_sudden"), ValueAtom("emergency room immediately")))
    metta.space().add_atom(E(S("warning_sign"), S("high_fever_103"), ValueAtom("urgent medical attention")))
    metta.space().add_atom(E(S("warning_sign"), S("persistent_vomiting"), ValueAtom("urgent care within 24 hours")))
    
    # Drug Interactions → Severity
    metta.space().add_atom(E(S("drug_interaction"), S("warfarin_aspirin"), ValueAtom("severe bleeding risk")))
    metta.space().add_atom(E(S("drug_interaction"), S("metformin_alcohol"), ValueAtom("lactic acidosis risk")))
    metta.space().add_atom(E(S("drug_interaction"), S("lisinopril_potassium"), ValueAtom("hyperkalemia risk")))
    metta.space().add_atom(E(S("drug_interaction"), S("statins_grapefruit"), ValueAtom("increased statin levels")))
    
    # Common Medical FAQs
    metta.space().add_atom(E(S("faq"), S("How often should I have a checkup?"), ValueAtom("Annual checkups for adults, more frequent if chronic conditions")))
    metta.space().add_atom(E(S("faq"), S("When should I see a doctor for fever?"), ValueAtom("Fever over 103°F, lasts more than 3 days, or with severe symptoms")))
    metta.space().add_atom(E(S("faq"), S("Is it safe to take expired medication?"), ValueAtom("No, expired medications may be ineffective or harmful")))
    metta.space().add_atom(E(S("faq"), S("How long should I wait between appointments?"), ValueAtom("Depends on condition: routine 1 year, chronic 3-6 months, acute as needed")))
    
    # Initialize reasoning rules
    _initialize_medical_reasoning_rules(metta)
    
    # Initialize patient-specific relationship encoding
    _initialize_patient_relationship_encoding(metta)


def _initialize_medical_reasoning_rules(metta: MeTTa):
    """Initialize logical reasoning rules for medical decision making."""
    
    # Symptom severity assessment rules
    metta.space().add_atom(E(S("="), 
        E(S("requires_urgent_care"), S("$patient"), S("$symptoms")),
        E(S("and"), 
            E(S("has_symptoms"), S("$patient"), S("$symptoms")),
            E(S("urgency_level"), S("$symptoms"), ValueAtom("urgent")))))
    
    # Medication suitability rules
    metta.space().add_atom(E(S("="), 
        E(S("safe_medication"), S("$patient"), S("$medication")),
        E(S("and"),
            E(S("age_safe_medication"), S("$age_group"), S("$medication")),
            E(S("not"), E(S("has_contraindication"), S("$patient"), S("$medication"))))))
    
    # Appointment scheduling priority rules
    metta.space().add_atom(E(S("="), 
        E(S("appointment_priority"), S("$condition"), S("$priority")),
        E(S("urgency_level"), S("$condition"), S("$priority"))))
    
    # Specialist referral rules
    metta.space().add_atom(E(S("="), 
        E(S("needs_specialist"), S("$condition"), S("$specialty")),
        E(S("specialty_condition"), S("$specialty"), S("$condition"))))
    
    # Treatment compatibility rules
    metta.space().add_atom(E(S("="), 
        E(S("appropriate_treatment"), S("$condition"), S("$treatment")),
        E(S("and"),
            E(S("treatment"), S("$condition"), S("$treatment")),
            E(S("suitable_for_patient"), S("$patient"), S("$treatment")))))
    
    # Drug interaction warning rules
    metta.space().add_atom(E(S("="), 
        E(S("interaction_risk"), S("$drug1"), S("$drug2")),
        E(S("or"),
            E(S("drug_interaction"), S("$drug1"), S("$drug2")),
            E(S("drug_interaction"), S("$drug2"), S("$drug1")))))
    
    # Preventive care timing rules
    metta.space().add_atom(E(S("="), 
        E(S("due_for_screening"), S("$patient"), S("$age_group")),
        E(S("and"),
            E(S("patient_age_group"), S("$patient"), S("$age_group")),
            E(S("preventive_care"), S("$age_group"), S("$screening")))))


def _initialize_patient_relationship_encoding(metta: MeTTa):
    """Initialize complex relationship encoding for patient care analysis."""
    
    # Symptom clusters and patterns
    metta.space().add_atom(E(S("symptom_cluster"), S("respiratory"), ValueAtom("cough, shortness_of_breath, chest_pain")))
    metta.space().add_atom(E(S("symptom_cluster"), S("gastrointestinal"), ValueAtom("nausea, vomiting, diarrhea, abdominal_pain")))
    metta.space().add_atom(E(S("symptom_cluster"), S("neurological"), ValueAtom("headache, dizziness, confusion, weakness")))
    metta.space().add_atom(E(S("symptom_cluster"), S("cardiovascular"), ValueAtom("chest_pain, palpitations, shortness_of_breath")))
    
    # Risk factor relationships
    metta.space().add_atom(E(S("risk_factor"), S("smoking"), S("lung_cancer"), ValueAtom("high")))
    metta.space().add_atom(E(S("risk_factor"), S("obesity"), S("diabetes"), ValueAtom("high")))
    metta.space().add_atom(E(S("risk_factor"), S("hypertension"), S("heart_disease"), ValueAtom("moderate")))
    metta.space().add_atom(E(S("risk_factor"), S("family_history"), S("genetic_conditions"), ValueAtom("variable")))
    
    # Medication effectiveness relationships
    metta.space().add_atom(E(S("medication_effectiveness"), S("antibiotics"), S("bacterial_infection"), ValueAtom("high")))
    metta.space().add_atom(E(S("medication_effectiveness"), S("antibiotics"), S("viral_infection"), ValueAtom("none")))
    metta.space().add_atom(E(S("medication_effectiveness"), S("antihistamines"), S("allergic_reaction"), ValueAtom("high")))
    metta.space().add_atom(E(S("medication_effectiveness"), S("nsaids"), S("inflammation"), ValueAtom("moderate")))
    
    # Follow-up timing relationships
    metta.space().add_atom(E(S("followup_timing"), S("acute_condition"), ValueAtom("1-2 weeks")))
    metta.space().add_atom(E(S("followup_timing"), S("chronic_condition"), ValueAtom("3-6 months")))
    metta.space().add_atom(E(S("followup_timing"), S("post_surgery"), ValueAtom("1-2 weeks")))
    metta.space().add_atom(E(S("followup_timing"), S("medication_adjustment"), ValueAtom("2-4 weeks")))
    
    # Lab test indication relationships
    metta.space().add_atom(E(S("lab_indication"), S("diabetes_screening"), S("blood_glucose"), ValueAtom("required")))
    metta.space().add_atom(E(S("lab_indication"), S("heart_disease"), S("cholesterol"), ValueAtom("required")))
    metta.space().add_atom(E(S("lab_indication"), S("anemia_symptoms"), S("complete_blood_count"), ValueAtom("required")))
    metta.space().add_atom(E(S("lab_indication"), S("kidney_function"), S("creatinine"), ValueAtom("required")))
    
    # Lifestyle modification relationships
    metta.space().add_atom(E(S("lifestyle_modification"), S("hypertension"), ValueAtom("low sodium diet, regular exercise")))
    metta.space().add_atom(E(S("lifestyle_modification"), S("diabetes"), ValueAtom("carb counting, regular monitoring")))
    metta.space().add_atom(E(S("lifestyle_modification"), S("high_cholesterol"), ValueAtom("low fat diet, increased fiber")))
    metta.space().add_atom(E(S("lifestyle_modification"), S("arthritis"), ValueAtom("low impact exercise, weight management")))
    
    # Emergency criteria relationships
    metta.space().add_atom(E(S("emergency_criteria"), S("heart_attack"), ValueAtom("chest pain, shortness of breath, nausea")))
    metta.space().add_atom(E(S("emergency_criteria"), S("stroke"), ValueAtom("sudden weakness, speech problems, confusion")))
    metta.space().add_atom(E(S("emergency_criteria"), S("severe_allergic_reaction"), ValueAtom("difficulty breathing, swelling, hives")))
    metta.space().add_atom(E(S("emergency_criteria"), S("diabetic_emergency"), ValueAtom("very high/low blood sugar, confusion")))