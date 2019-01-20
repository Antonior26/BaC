from django.urls import path
from Isolates.views import IsolateList, SpeciesView, SelectGroupView, PatientCreate, IsolateDetail, PatientUpdate, \
    IsolateCreate, IsolateUpdate, SampleResult

urlpatterns = [
    path(r'detail/<pk>', IsolateDetail.as_view(), name='isolate-detail-view'),
    path(r'results/<tool>/<pk>', SampleResult.as_view(), name='sample-result-view'),
    path(r'create', IsolateCreate.as_view(), name='create-isolate-view'),
    path(r'update/<pk>', IsolateUpdate.as_view(), name='update-isolate-view'),
    path(r'patient/update/<pk>', PatientUpdate.as_view(), name='update-patient-view'),
    path(r'group', SelectGroupView.as_view(), name='group-view'),
    path(r'patient', PatientCreate.as_view(), name='create-patient-view'),
    path(r'<rank>/<name>', SpeciesView.as_view(), name='species-view'),
    path(r'', IsolateList.as_view(), name='isolate-list'),

]
