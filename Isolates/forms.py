from django import forms

from Isolates.models import Patient, OntologyTerm, Isolate


def always_valid(value):
    return True


class PatientForm(forms.ModelForm):
    phenotypes = forms.CharField(
        required=False, validators=[always_valid], widget=forms.SelectMultiple(attrs={'multiple': "multiple"}))

    class Meta:
        model = Patient
        fields = ['identifier']

    def save(self, **kwargs):
        patient = super(PatientForm, self).save(**kwargs)
        phenotypes = eval(self.cleaned_data.get('phenotypes'))
        if phenotypes:
            patient.phenotype.all().delete()
            for phenotype in phenotypes:
                ontology, label, term_id, description = phenotype.split(':::')
                if not patient.phenotype.filter(ontology_term__term_id=term_id):
                    t, created = OntologyTerm.objects.get_or_create(term_id=term_id, defaults={
                        'ontology': ontology,
                        'label': label,
                        'description': description
                    })
                    patient.phenotype.create(ontology_term=t)
        return patient


class IsolateForm(forms.ModelForm):
    phenotypes = forms.CharField(required=False, validators=[always_valid],
                                 widget=forms.SelectMultiple(attrs={'multiple': "multiple"})
                                 )

    class Meta:
        model = Isolate
        fields = ['identifier', 'species', 'collection_date', 'culture_type', 'tissue_origin']

    def save(self, **kwargs):
        isolate = super(IsolateForm, self).save(**kwargs)
        phenotypes = eval(self.cleaned_data.get('phenotypes'))
        if phenotypes:
            isolate.phenotype.all().delete()
            for phenotype in phenotypes:
                ontology, term_id, label, description = phenotype.split(':::')
                if not isolate.phenotype.filter(ontology_term__term_id=term_id):
                    t, created = OntologyTerm.objects.get_or_create(term_id=term_id, defaults={
                        'ontology': ontology,
                        'label': label,
                        'description': description
                    })
                    isolate.phenotype.create(ontology_term=t)
        return isolate