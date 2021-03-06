# Copyright 2017 Capital One Services, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from .common import BaseTest
import time


class TestGlueConnections(BaseTest):

    def test_connections_query(self):
        session_factory = self.replay_flight_data("test_glue_query_resources")
        p = self.load_policy(
            {"name": "list-glue-connections", "resource": "glue-connection"},
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)

    def test_connection_subnet_filter(self):
        session_factory = self.replay_flight_data("test_glue_subnet_filter")
        p = self.load_policy(
            {
                "name": "glue-connection",
                "resource": "glue-connection",
                "filters": [
                    {"type": "subnet", "key": "tag:Name", "value": "Default-48"}
                ],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(
            resources[0]["PhysicalConnectionRequirements"]["SubnetId"],
            "subnet-3a334610",
        )

    def test_connection_sg_filter(self):
        session_factory = self.replay_flight_data("test_glue_sg_filter")
        p = self.load_policy(
            {
                "name": "glue-connection",
                "resource": "glue-connection",
                "filters": [
                    {"type": "security-group", "key": "GroupName", "value": "default"}
                ],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(
            resources[0]["PhysicalConnectionRequirements"]["SecurityGroupIdList"],
            ["sg-6c7fa917"],
        )

    def test_connection_delete(self):
        session_factory = self.replay_flight_data("test_glue_delete_connection")
        p = self.load_policy(
            {
                "name": "glue-connection",
                "resource": "glue-connection",
                "filters": [{"ConnectionType": "JDBC"}],
                "actions": [{"type": "delete"}],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        client = session_factory().client("glue")
        connections = client.get_connections()["ConnectionList"]
        self.assertFalse(connections)


class TestGlueDevEndpoints(BaseTest):

    def test_dev_endpoints_query(self):
        session_factory = self.replay_flight_data("test_glue_query_resources")
        p = self.load_policy(
            {"name": "list-glue-dev-endpoints", "resource": "glue-dev-endpoint"},
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)

    def test_dev_endpoints_delete(self):
        session_factory = self.replay_flight_data("test_glue_dev_endpoint_delete")
        p = self.load_policy(
            {
                "name": "glue-dev-endpoint-delete",
                "resource": "glue-dev-endpoint",
                "filters": [{"PublicAddress": "present"}],
                "actions": [{"type": "delete"}],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        client = session_factory().client("glue")
        dev_endpoints = client.get_dev_endpoints()["DevEndpoints"]
        self.assertFalse(dev_endpoints)


class TestGlueTag(BaseTest):

    def test_glue_tags(self):
        session_factory = self.replay_flight_data("test_glue_tags")
        client = session_factory().client("glue")

        tags = client.get_tags(ResourceArn='arn:aws:glue:us-east-1:644160558196:devEndpoint/test')
        self.assertEqual(tags.get('Tags'), {})

        policy = {
            'name': 'test',
            'resource': 'glue-dev-endpoint',
            'actions': [
                {
                    'type': 'tag',
                    'key': 'abcd',
                    'value': 'xyz'
                },
            ]
        }
        p = self.load_policy(
            policy,
            config={'account_id': '644160558196'},
            session_factory=session_factory)

        resources = p.run()
        arn = p.resource_manager.generate_arn(resources[0]['EndpointName'])
        self.assertEqual(arn, 'arn:aws:glue:us-east-1:644160558196:devEndpoint/test')
        tags = client.get_tags(ResourceArn=arn)
        self.assertEqual(len(resources), 1)
        self.assertEqual(tags.get('Tags'), {'abcd': 'xyz'})

    def test_glue_untag(self):
        session_factory = self.replay_flight_data("test_glue_untag")

        policy = {
            'name': 'test',
            'resource': 'glue-dev-endpoint',
            'actions': [{'type': 'remove-tag', 'tags': ['abcd']}]
        }
        p = self.load_policy(
            policy,
            config={'account_id': '644160558196'},
            session_factory=session_factory)

        resources = p.run()
        client = session_factory().client("glue")
        arn = p.resource_manager.generate_arn(resources[0]['EndpointName'])
        tags = client.get_tags(ResourceArn=arn)

        self.assertEqual(arn, 'arn:aws:glue:us-east-1:644160558196:devEndpoint/test')
        self.assertEqual(tags.get('Tags'), {})
        self.assertEqual(len(resources), 1)

    def test_glue_job_tag(self):
        session_factory = self.replay_flight_data("test_glue_job_tags")
        client = session_factory().client("glue")

        policy = {
            'name': 'test',
            'resource': 'glue-job',
            'filters': [{'tag:abcd': 'absent'}],
            'actions': [
                {
                    'type': 'tag',
                    'key': 'abcd',
                    'value': 'xyz'
                },
            ]
        }
        p = self.load_policy(
            policy,
            config={'account_id': '644160558196'},
            session_factory=session_factory)

        resources = p.run()
        arn = p.resource_manager.generate_arn(resources[0]['Name'])
        self.assertEqual(arn, 'arn:aws:glue:us-east-1:644160558196:job/test')
        tags = client.get_tags(ResourceArn=arn)
        self.assertEqual(len(resources), 1)
        self.assertEqual(tags.get('Tags'), {'abcd': 'xyz'})

    def test_glue_job_untag(self):
        session_factory = self.replay_flight_data("test_glue_job_untag")
        policy = {
            'name': 'test',
            'resource': 'glue-job',
            'filters': [{'tag:abcd': 'present'}],
            'actions': [{'type': 'remove-tag', 'tags': ['abcd']}]
        }
        p = self.load_policy(
            policy,
            config={'account_id': '644160558196'},
            session_factory=session_factory)

        resources = p.run()
        client = session_factory().client("glue")
        arn = p.resource_manager.generate_arn(resources[0]['Name'])
        tags = client.get_tags(ResourceArn=arn)

        self.assertEqual(arn, 'arn:aws:glue:us-east-1:644160558196:job/test')
        self.assertEqual(tags.get('Tags'), {})
        self.assertEqual(len(resources), 1)

    def test_glue_crawler_tag(self):
        session_factory = self.replay_flight_data("test_crawler_tags")
        client = session_factory().client("glue")

        policy = {
            'name': 'test',
            'resource': 'glue-crawler',
            'filters': [{'tag:abcd': 'absent'}],
            'actions': [
                {
                    'type': 'tag',
                    'key': 'abcd',
                    'value': 'xyz'
                },
            ]
        }
        p = self.load_policy(
            policy,
            config={'account_id': '644160558196'},
            session_factory=session_factory)

        resources = p.run()
        arn = p.resource_manager.generate_arn(resources[0]['Name'])
        self.assertEqual(arn, 'arn:aws:glue:us-east-1:644160558196:crawler/test')
        tags = client.get_tags(ResourceArn=arn)
        self.assertEqual(len(resources), 1)
        self.assertEqual(tags.get('Tags'), {'abcd': 'xyz'})

    def test_glue_crawler_untag(self):
        session_factory = self.replay_flight_data("test_glue_crawler_untag")

        policy = {
            'name': 'test',
            'resource': 'glue-crawler',
            'filters': [{'tag:abcd': 'present'}],
            'actions': [{'type': 'remove-tag', 'tags': ['abcd']}]
        }
        p = self.load_policy(
            policy,
            config={'account_id': '644160558196'},
            session_factory=session_factory)

        resources = p.run()
        client = session_factory().client("glue")
        arn = p.resource_manager.generate_arn(resources[0]['Name'])
        tags = client.get_tags(ResourceArn=arn)

        self.assertEqual(arn, 'arn:aws:glue:us-east-1:644160558196:crawler/test')
        self.assertEqual(tags.get('Tags'), {})
        self.assertEqual(len(resources), 1)


class TestGlueJobs(BaseTest):

    def test_jobs_delete(self):
        session_factory = self.replay_flight_data("test_glue_job_delete")
        p = self.load_policy(
            {
                "name": "glue-job-delete",
                "resource": "glue-job",
                "filters": [{"Name": "test"}],
                "actions": [{"type": "delete"}],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        client = session_factory().client("glue")
        jobs = client.get_jobs()["Jobs"]
        self.assertFalse(jobs)


class TestGlueCrawlers(BaseTest):

    def test_crawlers_delete(self):
        session_factory = self.replay_flight_data("test_glue_crawler_delete")
        p = self.load_policy(
            {
                "name": "glue-crawler-delete",
                "resource": "glue-crawler",
                "filters": [{"Name": "test"}],
                "actions": [{"type": "delete"}],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        client = session_factory().client("glue")
        crawlers = client.get_crawlers()["Crawlers"]
        self.assertFalse("test" in [c.get("Name") for c in crawlers])


class TestGlueTables(BaseTest):
    def test_tables_delete(self):
        session_factory = self.replay_flight_data("test_glue_table_delete")
        p = self.load_policy(
            {
                "name": "glue-table-delete",
                "resource": "glue-table",
                "filters": [{"Name": "test"}],
                "actions": [{"type": "delete"}],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        client = session_factory().client("glue")
        tables = client.get_tables(DatabaseName='test')["TableList"]
        self.assertFalse("test" in [t.get("Name") for t in tables])


class TestGlueDatabases(BaseTest):

    def test_databases_delete(self):
        session_factory = self.replay_flight_data("test_glue_database_delete")
        p = self.load_policy(
            {
                "name": "glue-database-delete",
                "resource": "glue-database",
                "filters": [{"Name": "test"}],
                "actions": [{"type": "delete"}],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        client = session_factory().client("glue")
        databases = client.get_databases()
        self.assertFalse("test" in [t.get("Name") for t in databases.get("DatabaseList", [])])


class TestGlueClassifiers(BaseTest):

    def test_classifiers_delete(self):
        session_factory = self.replay_flight_data("test_glue_classifier_delete")
        p = self.load_policy(
            {
                "name": "glue-classifier-delete",
                "resource": "glue-classifier",
                "filters": [{"CsvClassifier.Name": "test"}],
                "actions": [{"type": "delete"}],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        client = session_factory().client("glue")
        classifiers = client.get_classifiers()
        self.assertFalse("test" in [t.get('CsvClassifier').get("Name")
            for t in classifiers.get("Classifiers", [])])


class GlueMLTransform(BaseTest):

    def test_ml_transforms_delete(self):
        session_factory = self.replay_flight_data("test_glue_ml_transform_delete")
        p = self.load_policy(
            {
                "name": "glue-ml-transform-delete",
                "resource": "glue-ml-transform",
                "filters": [{"Name": 'test'}],
                "actions": [{"type": "delete"}],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        client = session_factory().client("glue")
        ml_transforms = client.get_ml_transforms()
        self.assertFalse("test" in [t.get("Name") for t in ml_transforms.get("Transforms", [])])


class TestGlueSecurityConfiguration(BaseTest):

    def test_security_configurations_delete(self):
        session_factory = self.replay_flight_data("test_glue_security_configuration_delete")
        p = self.load_policy(
            {
                "name": "glue-security-configuration-delete",
                "resource": "glue-security-configuration",
                "filters": [{"Name": "test"}],
                "actions": [{"type": "delete"}],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        client = session_factory().client("glue")
        security_configrations = client.get_security_configurations()
        self.assertFalse("test" in [t.get("Name")
            for t in security_configrations.get("SecurityConfigurations", [])])


class TestGlueTriggers(BaseTest):

    def test_triggers_delete(self):
        session_factory = self.replay_flight_data("test_glue_trigger_delete")
        p = self.load_policy(
            {
                "name": "glue-trigger-delete",
                "resource": "glue-trigger",
                "filters": [{"Name": "test"}],
                "actions": [{"type": "delete"}],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        if self.recording:
            time.sleep(60)
        client = session_factory().client("glue")
        triggers = client.get_triggers()
        self.assertFalse("test" in [t.get("Name") for t in triggers.get("Triggers", [])])


class TestGlueWorkflows(BaseTest):

    def test_workflows_delete(self):
        session_factory = self.replay_flight_data("test_glue_workflow_delete")
        p = self.load_policy(
            {
                "name": "glue-workflow-delete",
                "resource": "glue-workflow",
                "filters": [{"Name": "test"}],
                "actions": [{"type": "delete"}],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        client = session_factory().client("glue")
        workflows = client.list_workflows()
        self.assertFalse("test" in [t.get("Name") for t in workflows.get("Workflows", [])])


class TestGlueDataCatalog(BaseTest):

    def test_glue_datacat_put_encryption(self):
        session_factory = self.replay_flight_data("test_glue_datacat_put_encryption")
        client = session_factory().client("glue")
        cat_setting = client.get_data_catalog_encryption_settings()
        self.assertEqual(cat_setting.get('DataCatalogEncryptionSettings').get(
            'EncryptionAtRest').get('SseAwsKmsKeyId'), 'alias/skunk/trails')
        p = self.load_policy(
            {
                "name": "glue-security-config",
                "resource": "glue-catalog",
                'filters': [{
                    'type': 'value',
                    'key': 'DataCatalogEncryptionSettings.EncryptionAtRest.SseAwsKmsKeyId',
                    'value': 'alias/skunk/trails',
                    'op': 'eq'},
                ],
                "actions": [{
                    "type": "set-encryption",
                    "attributes": {
                        "EncryptionAtRest": {
                            "CatalogEncryptionMode": "SSE-KMS",
                            "SseAwsKmsKeyId": "alias/skunk/glue/encrypted"},
                    },
                }]
            },
            session_factory=session_factory,)

        resources = p.run()
        self.assertEqual(len(resources), 1)
        client = session_factory().client("glue")
        datacatlog = client.get_data_catalog_encryption_settings()
        self.assertEqual(datacatlog.get('DataCatalogEncryptionSettings').get(
            'EncryptionAtRest'),
            {'CatalogEncryptionMode': 'SSE-KMS', 'SseAwsKmsKeyId': 'alias/skunk/glue/encrypted'})

    def test_glue_catalog_cross_account(self):
        session_factory = self.replay_flight_data("test_glue_catalog_cross_account")
        p = self.load_policy(
            {
                "name": "glue-catalog-cross-account",
                "resource": "glue-catalog",
                "filters": [{"type": "cross-account"}],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
