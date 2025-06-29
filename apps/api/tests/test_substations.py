from rest_framework.test import APIClient, APITestCase

# from apps.api.models import Substations

client = APIClient()


class SubstationAPITests(APITestCase):
    substation_expected = {
        "sitefunctionallocation": "EPN-S0000000C1041",
        "licencearea": "Eastern Power Networks (EPN)",
        "sitename": "CLIFF QUAY GRID 132KV",
        "sitetype": "Grid Substation",
        "sitevoltage": 132,
        "esqcroverallrisk": "High",
        "gridref": "TM17074204",
        "siteassetcount": 67,
        "powertransformercount": 0,
        "electricalassetcount": 67,
        "civilassetcount": 0,
        "street": None,
        "suburb": None,
        "towncity": "IPSWICH SOUTH",
        "county": "Suffolk",
        "postcode": "IP3 0BS",
        "yearcommissioned": "NA",
        "datecommissioned": "2017-04-01",
        "siteclassification": "NA",
        "assessmentdate": None,
        "last_report": "NA",
        "calculatedresistance": "NA",
        "measuredresistance_ohm": None,
        "next_assessmentdate": "2037-11-30",
        "easting": "617070",
        "northing": "242040",
        "transratingwinter": "NA",
        "transratingsummer": "NA",
        "reversepower": "NA",
        "maxdemandsummer": "NA",
        "maxdemandwinter": "NA",
        "spatial_coordinates": {"lon": 1.16325674714046, "lat": 52.0342568413421},
        "local_authority": "Ipswich",
        "local_authority_code": "E07000202",
        "what3words": "shielding.compress.cope",
    }

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/v1/substations/"
        # Set up any necessary data here, such as creating a user and logging in
        # self.user = User.objects.create_user(username='testuser', password='testpass')
        # self.client.login(username='testuser', password='testpass')

    def test_list_substations(self):
        # Create expected substation data in database
        # substation = Substations.objects.create(**self.substation_expected)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.content, list)

        self.assertJSONEqual(
            response.content,
            [self.substation_expected],
            msg="Response data does not match expected substation data",
        )

    def test_get_substation_by_id(self):
        # Create a substation instance
        # substation = Substations.objects.create(**self.substation_expected)
        response = self.client.get(f"{self.url}{1}/")
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            self.substation_expected,
            msg="Response data does not match expected substation data",
        )
