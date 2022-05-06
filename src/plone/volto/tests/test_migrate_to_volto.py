from Acquisition import aq_base
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import SITE_OWNER_NAME, SITE_OWNER_PASSWORD
from plone.base.utils import get_installer
from plone.volto.content import FolderishDocument
from plone.volto.content import FolderishNewsItem
from plone.volto.content import FolderishEvent
from plone.volto.testing import PLONE_VOLTO_MIGRATION_FUNCTIONAL_TESTING

import unittest
import transaction


class TestMigrateToVolto(unittest.TestCase):

    layer = PLONE_VOLTO_MIGRATION_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.portal_url = self.portal.absolute_url()

    def test_form_renders(self):
        view = self.portal.restrictedTraverse("@@migrate_to_volto")
        html = view()
        self.assertIn("Migrate to Volto", html)

    def test_plonevolto_is_installed(self):
        installer = get_installer(self.portal, self.request)
        # self.assertTrue(installer.is_product_installable("plone.volto"))
        self.assertFalse(installer.is_product_installed("plone.volto"))

        view = self.portal.restrictedTraverse("@@migrate_to_volto")
        self.request.form["form.submitted"] = True
        view()

        self.assertTrue(installer.is_product_installed("plone.volto"))

    def test_items_are_migrated_to_folderish(self):
        doc = api.content.create(
            container=self.portal,
            type="Document",
            id="doc",
            title="Document",
        )
        news = api.content.create(
            container=self.portal,
            type="News Item",
            id="news",
            title="News Item",
        )
        doc = api.content.create(
            container=self.portal,
            type="Event",
            id="event",
            title="Event",
        )

        view = self.portal.restrictedTraverse("@@migrate_to_volto")
        self.request.form["form.submitted"] = True
        view()

        doc = self.portal["doc"]
        self.assertEqual(doc.portal_type, "Document")
        self.assertTrue(aq_base(doc).isPrincipiaFolderish)
        self.assertEqual(doc.__class__, FolderishDocument)

        news = self.portal["news"]
        self.assertEqual(news.portal_type, "News Item")
        self.assertTrue(aq_base(news).isPrincipiaFolderish)
        self.assertEqual(news.__class__, FolderishNewsItem)

        event = self.portal["event"]
        self.assertEqual(event.portal_type, "Event")
        self.assertTrue(aq_base(event).isPrincipiaFolderish)
        self.assertEqual(event.__class__, FolderishEvent)

    def test_folders_are_migrated(self):
        folder = api.content.create(
            container=self.portal,
            type="Folder",
            id="folder1",
            title="Folder 1",
        )
        self.assertEqual(self.portal["folder1"].portal_type, "Folder")

        view = self.portal.restrictedTraverse("@@migrate_to_volto")
        self.request.form["form.submitted"] = True
        view()

        doc = self.portal["folder1"]
        self.assertEqual(doc.portal_type, "Document")
        self.assertTrue(aq_base(doc).isPrincipiaFolderish)
        self.assertEqual(doc.__class__, FolderishDocument)

    def test_collections_are_migrated(self):
        folder = api.content.create(
            container=self.portal,
            type="Collection",
            id="collection",
            title="Collection",
        )
        self.assertEqual(self.portal["collection"].portal_type, "Collection")

        view = self.portal.restrictedTraverse("@@migrate_to_volto")
        self.request.form["form.submitted"] = True
        view()

        collection = self.portal["collection"]
        self.assertEqual(collection.portal_type, "Document")
        aq_base(collection).isPrincipiaFolderish
        self.assertTrue(aq_base(collection).isPrincipiaFolderish)
        self.assertEqual(collection.__class__, FolderishDocument)

    def test_default_pages_are_migrated(self):
        folder = api.content.create(
            container=self.portal,
            type="Folder",
            id="folder",
            title="Folder",
        )
        default = api.content.create(
            container=folder,
            type="Document",
            id="doc",
            title="Document",
            description="This is a default page",
        )
        folder.setDefaultPage("doc")

        view = self.portal.restrictedTraverse("@@migrate_to_volto")
        self.request.form["form.submitted"] = True
        view()

        folder = self.portal["folder"]
        self.assertEqual(folder.portal_type, "Document")
        self.assertIsNone(getattr(folder, "default_page", None))
        self.assertEqual(folder.title, "Document")
        self.assertEqual(folder.description, "This is a default page")

    def test_default_page_collections_are_migrated(self):
        folder = api.content.create(
            container=self.portal,
            type="Folder",
            id="folder",
            title="Folder",
        )
        default = api.content.create(
            container=folder,
            type="Collection",
            id="collection",
            title="Collection",
            description="This is a default collection",
        )
        folder.setDefaultPage("collection")
        self.assertIn("collection", folder.keys())

        view = self.portal.restrictedTraverse("@@migrate_to_volto")
        self.request.form["form.submitted"] = True
        view()

        folder = self.portal["folder"]
        self.assertEqual(folder.portal_type, "Document")
        self.assertIsNone(getattr(folder, "default_page", None))
        self.assertNotIn("collection", folder.keys())
        self.assertEqual(folder.title, "Collection")
        self.assertEqual(folder.description, "This is a default collection")

    def test_default_page_news_are_not_migrated(self):
        folder = api.content.create(
            container=self.portal,
            type="Folder",
            id="folder",
            title="Folder",
            description="This of the folder",
        )
        default = api.content.create(
            container=folder,
            type="News Item",
            id="news",
            title="News Item",
            description="This is a default news item",
        )
        folder.setDefaultPage("news")
        self.assertIn("news", folder.keys())

        view = self.portal.restrictedTraverse("@@migrate_to_volto")
        self.request.form["form.submitted"] = True
        view()

        folder = self.portal["folder"]
        self.assertEqual(folder.portal_type, "Document")
        # the default_page attr is not removed
        self.assertEqual(folder.default_page, "news")
        self.assertEqual(folder.title, "Folder")
        self.assertEqual(folder.description, "This of the folder")

        self.assertIn("news", folder.keys())
        self.assertEqual(folder["news"].portal_type, "News Item")
        self.assertEqual(folder["news"].title, "News Item")
        self.assertEqual(folder["news"].description, "This is a default news item")
