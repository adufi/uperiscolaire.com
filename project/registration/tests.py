import json

from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework.views import status

from .models import ChildPAI, ChildQuotient, ChildClass, Sibling, SiblingChild, SiblingIntels, Family, Record, CAF, Health
from .serializers import FamilySerializer, RecordSerializer

from users.models import User

# tests for views

class BaseViewTest(APITestCase):
    client = APIClient()

    @staticmethod
    def create_family(parent=0, child=0):
        if parent != 0 and child != 0:
            Family.objects.create(parent=parent, child=child)

    def setUp(self):
        # add test data
        self.create_family(17, 20)
        self.create_family(17, 21)
        self.create_family(17, 22)

        self.create_family(18, 23)
        self.create_family(18, 24)
        self.create_family(18, 25)

        self.create_family(19, 26)
        self.create_family(19, 27)
        self.create_family(19, 28)

"""
class GetAllFamilyTest(BaseViewTest):

    def test_get_all_family(self):
        ""
        This test ensures that all family added in the setUp method
        exist when we make a GET request to the family/ endpoint
        ""
        # hit the API endpoint
        response = self.client.get(
            reverse("family-all", kwargs={"version": "v1"})
        )
        # fetch the data from db
        expected = Family.objects.all()
        serialized = FamilySerializer(expected, many=True)
        self.assertEqual(response.data, serialized.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
"""

class BaseViewTest(APITestCase):
    client = APIClient()

    def setUp(self):
        # add test data
        return None
 

class BaseRegistrationTests(BaseViewTest):

    def setUp(self):
        self.parent = User.objects.create(
            last_name='Test',
            first_name='Parent'
        )

        self.child = User.objects.create(
            last_name='Test',
            first_name='Child '
        )

        self.sibling = Sibling.objects.create(parent=self.parent.id)


    def test_sibling_add_child(self):
        # print ('test_sibling_add_child')

        # print ('parent ({})'.format(self.parent.id))
        # print ('child ({})'.format(self.child.id))

        self.sibling.add_child(self.child.id)

        children = self.sibling.children.all()
        # print (children)

        self.assertTrue(self.sibling.children.get(child=self.child.id))


    def test_sibling_remove_child(self):
        self.sibling.add_child(self.child.id)
        self.sibling.remove_child(self.child.id)

        self.assertFalse(self.sibling.children.filter(child=self.child.id))


    def test_sibling_switch_child(self):
        sibling = Sibling.objects.create()
        sibling.add_child(self.child.id)

        self.sibling.add_child(self.child.id)

        self.assertTrue(self.sibling.children.get(child=self.child.id))
        self.assertFalse(sibling.children.filter(child=self.child.id))


    def test_sibling_add_intels(self):
        sibling = Sibling.objects.create()
        sibling.add_intels({
            'quotient_q1': ChildQuotient.Q1,
            'quotient_q2': ChildQuotient.Q2,

            'recipent_number': 0,
            'insurance_policy': 0
        }, 0)

        self.assertTrue(sibling.intels.all())


    def test_sibling_remove_intels(self):
        sibling = Sibling.objects.create()
        intel = sibling.add_intels({
            'quotient_q1': ChildQuotient.Q1,
            'quotient_q2': ChildQuotient.Q2,

            'recipent_number': 0,
            'insurance_policy': 0
        }, 0)

        sibling.remove_intels(intel.id)
        self.assertFalse(sibling.intels.all())


"""
class RecordTest(BaseViewTest):

    record_payload = {
        "school": "GOND",
        "classroom": 5,
        "child_id": 78,
        "caf": {
            "q1": 1,
            "q2": 2,
            "recipent_number": 0
        },
        "health": {
            "asthme": True,
            "allergy_food": True,
            "allergy_drug": True,
            "allergy_food_details": "...",
            "allergy_drug_details": "...",
            "pai": 2
        }
    }

    def test_admin_add_record(self):
        
        # hit the API endpoint
        response = self.client.post(
            reverse('record_add', kwargs={'version': 'v1'}),
            json.dumps(self.record_payload),
            content_type='application/json'
        )

        # fetch the data from db
        expected = Record.objects.filter(child_id=78).first()
        serialized = RecordSerializer(expected)

        self.assertEqual(response.data, serialized.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_add_record_invalid_payload(self):
        # hit the API endpoint
        response = self.client.post(
            reverse('record_add', kwargs={'version': 'v1'}),
            json.dumps({}),
            content_type='application/json'
        )

        data = json.loads(response.content)

        # fetch the data from db
        self.assertIn('Fail', data['status'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
"""