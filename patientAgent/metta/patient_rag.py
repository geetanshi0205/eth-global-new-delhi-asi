import re
import json
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from hyperon import MeTTa, E, S, ValueAtom
from datetime import datetime

class PatientRAG:
    def __init__(self, metta_instance: MeTTa):
        self.metta = metta_instance
        
        # Patient-specific learning components
        self.patient_learning_weights = {}
        self.symptom_feedback_history = []
        self.appointment_preferences = {}
        self._initialize_patient_neuro_symbolic_rules()

    def query_symptoms_conditions(self, symptoms: List[str]):
        """Enhanced symptom to condition mapping with nested queries."""
        all_conditions = []
        
        for symptom in symptoms:
            symptom = symptom.strip().lower().replace(" ", "_")
            
            # First get basic symptom-condition mappings
            simple_query = f'!(match &self (symptom_condition {symptom} $condition) $condition)'
            simple_results = self.metta.run(simple_query)
            
            if simple_results:
                for result in simple_results:
                    if result:
                        condition = str(result[0])
                        
                        # Get urgency for this condition
                        urgency_query = f'!(match &self (urgency_level {condition} $urgency) $urgency)'
                        urgency_results = self.metta.run(urgency_query)
                        urgency = urgency_results[0][0].get_object().value if urgency_results and urgency_results[0] else 'unknown'
                        
                        # Get treatment for this condition
                        treatment_query = f'!(match &self (treatment {condition} $treatment) $treatment)'
                        treatment_results = self.metta.run(treatment_query)
                        treatment = treatment_results[0][0].get_object().value if treatment_results and treatment_results[0] else 'assessment needed'
                        
                        all_conditions.append({
                            'symptom': symptom,
                            'condition': condition,
                            'urgency': urgency,
                            'treatment': treatment
                        })
        
        return all_conditions

    def get_medication_info(self, medication: str):
        """Get comprehensive medication information."""
        medication = medication.strip().lower()
        
        # Query for dosage information
        dosage_query = f'!(match &self (medication_dosage {medication} $dosage) $dosage)'
        dosage_results = self.metta.run(dosage_query)
        
        # Query for contraindications
        contraindication_query = f'!(match &self (contraindication {medication} $contra) $contra)'
        contra_results = self.metta.run(contraindication_query)
        
        # Query for drug interactions
        interaction_query = f'!(match &self (drug_interaction {medication} $other_drug) $other_drug)'
        interaction_results = self.metta.run(interaction_query)
        
        return {
            'medication': medication,
            'dosage': [r[0].get_object().value for r in dosage_results if r and len(r) > 0] if dosage_results else [],
            'contraindications': [r[0].get_object().value for r in contra_results if r and len(r) > 0] if contra_results else [],
            'interactions': [str(r[0]) for r in interaction_results if r and len(r) > 0] if interaction_results else []
        }

    def get_preventive_care_recommendations(self, age_group: str):
        """Get age-appropriate preventive care recommendations."""
        age_group = age_group.strip().lower()
        query_str = f'!(match &self (preventive_care {age_group} $care) $care)'
        results = self.metta.run(query_str)
        
        return [r[0].get_object().value for r in results if r and len(r) > 0] if results else []

    def assess_urgency_level(self, symptoms: List[str], patient_context: Dict = None):
        """Assess overall urgency level based on symptoms and patient context."""
        urgency_levels = {'emergency': 4, 'urgent': 3, 'moderate': 2, 'routine': 1, 'unknown': 0}
        max_urgency = 0
        max_urgency_condition = None
        
        conditions = self.query_symptoms_conditions(symptoms)
        
        for condition_info in conditions:
            urgency = condition_info.get('urgency', 'unknown')
            if urgency in urgency_levels:
                urgency_score = urgency_levels[urgency]
                if urgency_score > max_urgency:
                    max_urgency = urgency_score
                    max_urgency_condition = condition_info['condition']
        
        # Convert back to text
        urgency_text = next((k for k, v in urgency_levels.items() if v == max_urgency), 'unknown')
        
        return {
            'urgency_level': urgency_text,
            'primary_concern': max_urgency_condition,
            'all_conditions': conditions,
            'recommendation': self._get_urgency_recommendation(urgency_text)
        }

    def _get_urgency_recommendation(self, urgency: str):
        """Get recommendation based on urgency level."""
        recommendations = {
            'emergency': 'Seek immediate emergency care or call 911',
            'urgent': 'Schedule urgent appointment within 24 hours',
            'moderate': 'Schedule appointment within 1-2 weeks',
            'routine': 'Schedule routine appointment within 1 month',
            'unknown': 'Consult with healthcare provider for assessment'
        }
        return recommendations.get(urgency, recommendations['unknown'])

    def check_medication_safety(self, medications: List[str], patient_age_group: str = "adult"):
        """Check medication safety including age appropriateness and interactions."""
        safety_report = {
            'safe_medications': [],
            'unsafe_medications': [],
            'interactions': [],
            'age_concerns': []
        }
        
        # Check age safety for each medication
        for med in medications:
            med = med.strip().lower()
            age_safe_query = f'!(match &self (age_safe_medication {patient_age_group} {med}) {med})'
            age_safe_results = self.metta.run(age_safe_query)
            
            if age_safe_results:
                safety_report['safe_medications'].append(med)
            else:
                safety_report['age_concerns'].append(med)
        
        # Check for drug interactions
        for i, med1 in enumerate(medications):
            for med2 in medications[i+1:]:
                med1, med2 = med1.strip().lower(), med2.strip().lower()
                interaction_query = f'!(match &self (drug_interaction {med1} {med2}) $risk)'
                interaction_results = self.metta.run(interaction_query)
                
                if interaction_results:
                    risk = interaction_results[0][0].get_object().value if interaction_results[0] else "unknown risk"
                    safety_report['interactions'].append({
                        'drug1': med1,
                        'drug2': med2,
                        'risk': risk
                    })
        
        return safety_report

    def get_specialist_recommendation(self, conditions: List[str]):
        """Recommend appropriate specialist based on conditions."""
        specialists = {}
        
        for condition in conditions:
            condition = condition.strip().lower().replace(" ", "_")
            specialist_query = f'!(match &self (specialty_condition $specialty {condition}) $specialty)'
            results = self.metta.run(specialist_query)
            
            for result in results:
                if result:
                    specialty = str(result[0])
                    if specialty not in specialists:
                        specialists[specialty] = []
                    specialists[specialty].append(condition)
        
        return specialists

    def analyze_lab_results(self, lab_tests: Dict[str, float]):
        """Analyze lab results against normal ranges."""
        analysis = {}
        
        for test_name, value in lab_tests.items():
            test_name = test_name.strip().lower().replace(" ", "_")
            range_query = f'!(match &self (lab_normal_range {test_name} $range) $range)'
            results = self.metta.run(range_query)
            
            if results and results[0]:
                normal_range = results[0][0].get_object().value
                analysis[test_name] = {
                    'value': value,
                    'normal_range': normal_range,
                    'status': self._assess_lab_value(test_name, value, normal_range)
                }
            else:
                analysis[test_name] = {
                    'value': value,
                    'normal_range': 'Unknown',
                    'status': 'Requires professional interpretation'
                }
        
        return analysis

    def _assess_lab_value(self, test_name: str, value: float, normal_range: str):
        """Simple assessment of lab values (basic implementation)."""
        # This is a simplified implementation - in practice, you'd need more sophisticated parsing
        if "mg/dL" in normal_range:
            if "70-100" in normal_range and test_name == "blood_glucose":
                if 70 <= value <= 100:
                    return "Normal"
                elif value > 100:
                    return "High - possible diabetes risk"
                else:
                    return "Low - hypoglycemia risk"
        
        return "Requires professional interpretation"

    def get_appointment_duration_recommendation(self, appointment_type: str):
        """Get recommended duration for appointment type."""
        appointment_type = appointment_type.strip().lower().replace(" ", "_")
        duration_query = f'!(match &self (appointment_duration {appointment_type} $duration) $duration)'
        results = self.metta.run(duration_query)
        
        return results[0][0].get_object().value if results and results[0] else "30 minutes (standard)"

    def comprehensive_patient_assessment(self, patient_data: Dict):
        """Comprehensive assessment combining symptoms, medications, and patient history."""
        assessment = {
            'patient_id': patient_data.get('patient_id'),
            'timestamp': datetime.now().isoformat(),
            'symptom_analysis': {},
            'medication_safety': {},
            'urgency_assessment': {},
            'specialist_recommendations': {},
            'preventive_care': {},
            'follow_up_recommendations': {}
        }
        
        # Analyze symptoms if provided
        symptoms = patient_data.get('symptoms', [])
        if symptoms:
            assessment['symptom_analysis'] = self.query_symptoms_conditions(symptoms)
            assessment['urgency_assessment'] = self.assess_urgency_level(symptoms, patient_data)
            
            # Get conditions for specialist recommendations
            conditions = [item['condition'] for item in assessment['symptom_analysis']]
            assessment['specialist_recommendations'] = self.get_specialist_recommendation(conditions)
        
        # Analyze medications if provided
        medications = patient_data.get('medications', [])
        if medications:
            age_group = patient_data.get('age_group', 'adult')
            assessment['medication_safety'] = self.check_medication_safety(medications, age_group)
        
        # Get preventive care recommendations
        age_group = patient_data.get('age_group')
        if age_group:
            assessment['preventive_care'] = {
                'age_group': age_group,
                'recommendations': self.get_preventive_care_recommendations(age_group)
            }
        
        # Analyze lab results if provided
        lab_results = patient_data.get('lab_results', {})
        if lab_results:
            assessment['lab_analysis'] = self.analyze_lab_results(lab_results)
        
        return assessment

    def add_patient_knowledge(self, relation_type: str, subject: str, object_value: str):
        """Add new patient-specific knowledge dynamically."""
        if isinstance(object_value, str):
            object_value = ValueAtom(object_value)
        self.metta.space().add_atom(E(S(relation_type), S(subject), object_value))
        return f"Added {relation_type}: {subject} → {object_value}"

    def query_faq(self, question: str):
        """Retrieve medical FAQ answers."""
        query_str = f'!(match &self (faq "{question}" $answer) $answer)'
        results = self.metta.run(query_str)
        
        return results[0][0].get_object().value if results and results[0] else None

    def get_warning_signs_action(self, warning_sign: str):
        """Get immediate action for warning signs."""
        warning_sign = warning_sign.strip().lower().replace(" ", "_")
        action_query = f'!(match &self (warning_sign {warning_sign} $action) $action)'
        results = self.metta.run(action_query)
        
        return results[0][0].get_object().value if results and results[0] else "Consult healthcare provider"

    def _initialize_patient_neuro_symbolic_rules(self):
        """Initialize adaptive learning rules for patient-specific patterns."""
        
        # Patient preference learning
        self.metta.space().add_atom(E(S("="),
            E(S("patient_preference"), S("$patient"), S("$preference_type"), S("$value")),
            E(S("learned_from_history"), S("$patient"), S("$preference_type"), S("$value"))))
        
        # Symptom pattern recognition
        self.metta.space().add_atom(E(S("="),
            E(S("symptom_pattern"), S("$patient"), S("$pattern")),
            E(S("recurring_symptoms"), S("$patient"), S("$pattern"))))
        
        # Treatment effectiveness tracking
        self.metta.space().add_atom(E(S("="),
            E(S("treatment_effectiveness"), S("$patient"), S("$treatment"), S("$effectiveness")),
            E(S("outcome_tracking"), S("$patient"), S("$treatment"), S("$effectiveness"))))
        
        # Risk factor assessment
        self.metta.space().add_atom(E(S("="),
            E(S("patient_risk_level"), S("$patient"), S("$condition"), S("$risk")),
            E(S("calculate_risk"), S("$patient"), S("$condition"), S("$risk"))))

    def learn_from_patient_outcome(self, patient_id: str, symptoms: List[str], 
                                 treatment: str, outcome_score: float):
        """Learn from patient treatment outcomes."""
        # Store outcome in learning history
        outcome_record = {
            'patient_id': patient_id,
            'symptoms': symptoms,
            'treatment': treatment,
            'outcome_score': outcome_score,
            'timestamp': datetime.now().isoformat()
        }
        self.symptom_feedback_history.append(outcome_record)
        
        # Update learning weights
        for symptom in symptoms:
            weight_key = f"{patient_id}_{symptom}_{treatment}"
            if weight_key not in self.patient_learning_weights:
                self.patient_learning_weights[weight_key] = 0.5
            
            # Adaptive learning
            learning_rate = 0.1
            self.patient_learning_weights[weight_key] += learning_rate * (outcome_score - self.patient_learning_weights[weight_key])
            
            # Update symbolic knowledge
            effectiveness_value = ValueAtom(str(round(self.patient_learning_weights[weight_key], 3)))
            self.metta.space().add_atom(
                E(S("treatment_effectiveness"), S(patient_id), S(treatment), effectiveness_value)
            )
        
        return self.patient_learning_weights.get(weight_key, 0.5)

    def get_personalized_recommendations(self, patient_id: str, current_symptoms: List[str]):
        """Get personalized recommendations based on patient history."""
        recommendations = []
        
        # Query for patient-specific treatment effectiveness
        effectiveness_query = f'!(match &self (treatment_effectiveness {patient_id} $treatment $effectiveness) ($treatment $effectiveness))'
        results = self.metta.run(effectiveness_query)
        
        for result in results:
            if result and len(result) >= 2:
                treatment = str(result[0])
                # Handle the effectiveness value extraction more carefully
                effectiveness_atom = result[1]
                try:
                    if hasattr(effectiveness_atom, 'get_object'):
                        effectiveness = float(effectiveness_atom.get_object().value.strip('"'))
                    else:
                        effectiveness = float(str(effectiveness_atom).strip('"'))
                except (ValueError, AttributeError):
                    effectiveness = 0.5  # Default value
                
                if effectiveness > 0.6:  # Threshold for good effectiveness
                    recommendations.append({
                        'treatment': treatment,
                        'effectiveness_score': effectiveness,
                        'reason': f"Previously effective for {patient_id}"
                    })
        
        # Sort by effectiveness
        recommendations.sort(key=lambda x: x['effectiveness_score'], reverse=True)
        return recommendations

    def detect_symptom_patterns(self, patient_id: str, symptom_history: List[Dict]):
        """Detect recurring symptom patterns for a patient."""
        patterns = {}
        
        for record in symptom_history:
            symptoms = record.get('symptoms', [])
            date = record.get('date')
            
            # Look for symptom combinations
            symptom_combo = "_".join(sorted(symptoms))
            if symptom_combo not in patterns:
                patterns[symptom_combo] = []
            patterns[symptom_combo].append(date)
        
        # Identify recurring patterns (3 or more occurrences)
        recurring_patterns = {k: v for k, v in patterns.items() if len(v) >= 3}
        
        # Store patterns in knowledge graph
        for pattern, dates in recurring_patterns.items():
            pattern_value = ValueAtom(f"Recurring pattern: {len(dates)} occurrences")
            self.metta.space().add_atom(
                E(S("symptom_pattern"), S(patient_id), S(pattern), pattern_value)
            )
        
        return recurring_patterns

    def get_patient_risk_assessment(self, patient_data: Dict):
        """Comprehensive risk assessment for patient."""
        risk_factors = patient_data.get('risk_factors', [])
        family_history = patient_data.get('family_history', [])
        lifestyle = patient_data.get('lifestyle', {})
        
        risk_assessment = {}
        
        # Query risk factors
        for risk_factor in risk_factors:
            risk_query = f'!(match &self (risk_factor {risk_factor} $condition $level) ($condition $level))'
            results = self.metta.run(risk_query)
            
            for result in results:
                if result and len(result) >= 2:
                    condition, level = str(result[0]), str(result[1])
                    if condition not in risk_assessment:
                        risk_assessment[condition] = []
                    risk_assessment[condition].append({
                        'risk_factor': risk_factor,
                        'level': level
                    })
        
        return risk_assessment