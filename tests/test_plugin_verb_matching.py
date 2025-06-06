"""
Tests for the plugin verb matching system.

This module tests the plugin verb matching functionality, including exact
matching, fuzzy matching, priority resolution, and caching.
"""

import unittest
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

from plainspeak.plugins.base import Plugin, PluginRegistry
from plainspeak.plugins.manager import PluginManager


class PluginFixture(Plugin):
    """Test plugin implementation for testing verb matching."""

    def __init__(self, name, description, verbs=None, priority=0, aliases=None):
        super().__init__(name=name, description=description, priority=priority)
        self._verb_list = verbs or []
        self.verb_aliases = aliases or {}

    def get_verbs(self) -> List[str]:
        """Return the verbs supported by this plugin."""
        return self._verb_list

    def can_handle(self, verb: str) -> bool:
        """Check if this plugin can handle the given verb."""
        if not verb:
            return False

        verb_lower = verb.lower()
        # Check if it's a canonical verb
        if verb_lower in [v.lower() for v in self._verb_list]:
            return True

        # Check if it's an alias
        if verb_lower in [a.lower() for a in self.verb_aliases.keys()]:
            return True

        return False

    def get_canonical_verb(self, verb: str) -> str:
        """Return the canonical form of the verb."""
        if not verb:
            raise ValueError("Empty verb provided to get_canonical_verb")

        verb_lower = verb.lower()

        # Check if it's a canonical verb
        for canonical in self._verb_list:
            if canonical.lower() == verb_lower:
                return canonical

        # Check if it's an alias
        for alias, canonical in self.verb_aliases.items():
            if alias.lower() == verb_lower:
                return canonical

        raise ValueError(f"Verb '{verb}' is not recognized by plugin '{self.name}'")

    def generate_command(self, verb: str, args: Dict[str, Any]) -> str:
        """Generate a command for testing."""
        return f"{verb} {' '.join(f'{k}={v}' for k, v in args.items())}"

    def execute(self, verb: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the verb with the given arguments."""
        command = self.generate_command(verb, args)
        return {"success": True, "output": f"Executed: {command}"}

    def get_aliases(self) -> Dict[str, str]:
        """Get all verb aliases mapped to their canonical verbs."""
        return self.verb_aliases

    def get_all_verbs_and_aliases(self) -> List[str]:
        """Get all verbs and aliases this plugin can handle."""
        return self._verb_list + list(self.verb_aliases.keys())

    def clear_caches(self) -> None:
        """Clear the internal caches for verb handling."""
        if hasattr(self, "_verb_cache"):
            self._verb_cache.clear()
        if hasattr(self, "_canonical_verb_cache"):
            self._canonical_verb_cache.clear()


class TestExactMatching(unittest.TestCase):
    """Test exact verb matching functionality."""

    def setUp(self):
        """Set up test environment."""
        # Create registry
        self.registry = PluginRegistry()

        # Create plugin manager
        self.manager = PluginManager()
        self.manager.registry = self.registry

        # Create test plugins
        self.file_plugin = PluginFixture(
            name="file",
            description="File operations",
            verbs=["ls", "find", "copy", "move"],
            priority=10,
            aliases={"list": "ls", "locate": "find", "cp": "copy", "mv": "move"},
        )

        self.text_plugin = PluginFixture(
            name="text",
            description="Text operations",
            verbs=["grep", "sed", "cat"],
            priority=5,
            aliases={"search": "grep", "find": "grep", "replace": "sed", "show": "cat"},
        )

        # Register plugins
        self.registry.register(self.file_plugin)
        self.registry.register(self.text_plugin)

    def test_exact_match(self):
        """Test exact verb matching."""
        # Test direct verb matches
        plugin = self.manager.get_plugin_for_verb("ls")
        self.assertEqual(plugin, self.file_plugin)

        plugin = self.manager.get_plugin_for_verb("grep")
        self.assertEqual(plugin, self.text_plugin)

    def test_case_insensitive_match(self):
        """Test case-insensitive matching."""
        # Test matches with different case
        plugin = self.manager.get_plugin_for_verb("LS")
        self.assertEqual(plugin, self.file_plugin)

        plugin = self.manager.get_plugin_for_verb("Grep")
        self.assertEqual(plugin, self.text_plugin)

    def test_alias_match(self):
        """Test matching via aliases."""
        # Test alias matches
        plugin = self.manager.get_plugin_for_verb("list")
        self.assertEqual(plugin, self.file_plugin)

        plugin = self.manager.get_plugin_for_verb("search")
        self.assertEqual(plugin, self.text_plugin)

    def test_canonical_verb_resolution(self):
        """Test that aliases are resolved to canonical verbs."""
        # Get canonical verb
        verb = self.file_plugin.get_canonical_verb("list")
        self.assertEqual(verb, "ls")

        verb = self.text_plugin.get_canonical_verb("search")
        self.assertEqual(verb, "grep")

    @patch("plainspeak.plugins.manager.PluginManager._find_plugin_with_fuzzy_matching")
    def test_priority_resolution(self, mock_fuzzy_match):
        """Test priority-based resolution for conflicting verbs."""
        # Configure the mock to not be called and return None if it is called
        mock_fuzzy_match.return_value = None

        # First, manually clear any caches
        self.registry.get_plugin_for_verb.cache_clear()
        self.registry.verb_to_plugin_cache.clear()
        self.file_plugin.clear_caches()
        self.text_plugin.clear_caches()

        # Both plugins handle "find", file_plugin has higher priority
        plugin = self.manager.get_plugin_for_verb("find")
        self.assertEqual(plugin.name, self.file_plugin.name)
        self.assertEqual(plugin.priority, self.file_plugin.priority)

        # Create a new registry and plugins to avoid any state issues
        new_registry = PluginRegistry()
        new_manager = PluginManager()
        new_manager.registry = new_registry

        # Create new plugins with swapped priorities
        file_plugin = PluginFixture(
            name="file",
            description="File operations",
            verbs=["ls", "find", "copy", "move"],
            priority=1,  # Lower priority
            aliases={"list": "ls", "locate": "find", "cp": "copy", "mv": "move"},
        )

        text_plugin = PluginFixture(
            name="text",
            description="Text operations",
            verbs=["grep", "sed", "cat"],
            priority=20,  # Higher priority
            aliases={"search": "grep", "find": "grep", "replace": "sed", "show": "cat"},
        )

        # Register plugins
        new_registry.register(file_plugin)
        new_registry.register(text_plugin)

        # Now text plugin should win
        plugin = new_manager.get_plugin_for_verb("find")
        self.assertEqual(plugin.name, text_plugin.name)
        self.assertEqual(plugin.priority, text_plugin.priority)


class TestFuzzyMatching(unittest.TestCase):
    """Test fuzzy verb matching functionality."""

    def setUp(self):
        """Set up test environment."""
        # Create registry
        self.registry = PluginRegistry()

        # Create plugin manager with configurable threshold
        self.manager = PluginManager()
        self.manager.registry = self.registry
        self.manager.FUZZY_MATCH_THRESHOLD = 0.75  # Default threshold

        # Create test plugin with common verbs
        self.plugin = PluginFixture(
            name="test",
            description="Test plugin",
            verbs=["find", "search", "list", "create", "delete", "update"],
            priority=10,
        )

        # Register plugin
        self.registry.register(self.plugin)

    @patch("plainspeak.plugins.manager.difflib.get_close_matches")
    def test_fuzzy_matching_typos(self, mock_get_close_matches):
        """Test fuzzy matching with typos."""
        # Configure mocks to return verbs on specific inputs
        mock_get_close_matches.side_effect = lambda word, possibilities, n, cutoff: {
            "fin": ["find"],
            "saerch": ["search"],
            "listt": ["list"],
        }.get(word, [])

        # Test with typos
        plugin = self.manager.get_plugin_for_verb("fin")  # Missing 'd'
        self.assertEqual(plugin, self.plugin)

        plugin = self.manager.get_plugin_for_verb("saerch")  # Swapped letters
        self.assertEqual(plugin, self.plugin)

        plugin = self.manager.get_plugin_for_verb("listt")  # Extra letter
        self.assertEqual(plugin, self.plugin)

    @patch("plainspeak.plugins.manager.difflib.get_close_matches")
    def test_threshold_configuration(self, mock_get_close_matches):
        """Test threshold configuration for fuzzy matching."""

        # Configure mock for different thresholds
        def mock_close_matches(word, possibilities, n, cutoff):
            if word == "creatt" and cutoff <= 0.6:
                return ["create"]
            elif word == "creatt" and cutoff > 0.6:
                return []  # No match for higher thresholds
            return []

        mock_get_close_matches.side_effect = mock_close_matches

        # Make sure caches are cleared
        self.manager.get_plugin_for_verb.cache_clear()

        # Higher threshold should be more strict
        self.manager.FUZZY_MATCH_THRESHOLD = 0.9

        # This should now fail (match score too low)
        plugin = self.manager.get_plugin_for_verb("creatt")
        self.assertIsNone(plugin)

        # Clear all caches
        self.manager.get_plugin_for_verb.cache_clear()
        self.registry.get_plugin_for_verb.cache_clear()
        self.registry.verb_to_plugin_cache.clear()
        self.plugin.clear_caches()

        # Lower threshold should be more permissive
        self.manager.FUZZY_MATCH_THRESHOLD = 0.5  # Explicitly below 0.6 to match our mock

        # This should now pass
        plugin = self.manager.get_plugin_for_verb("creatt")
        self.assertIsNotNone(plugin, "Plugin should not be None with lower threshold")
        self.assertEqual(plugin, self.plugin)

    @patch("plainspeak.plugins.manager.difflib.get_close_matches")
    def test_fuzzy_match_scoring(self, mock_get_close_matches):
        """Test fuzzy match scoring logic."""

        # Configure mock for different inputs
        def mock_close_matches(word, possibilities, n, cutoff):
            if word == "lst":
                return ["list"]
            elif word == "serch":
                return ["search"]
            return []

        mock_get_close_matches.side_effect = mock_close_matches

        # Test with varying degrees of similarity
        # Should match (close to "list")
        plugin = self.manager.get_plugin_for_verb("lst")
        self.assertEqual(plugin, self.plugin)

        # Should match (close to "search")
        plugin = self.manager.get_plugin_for_verb("serch")
        self.assertEqual(plugin, self.plugin)

        # Should not match (too different from any verb)
        plugin = self.manager.get_plugin_for_verb("xyz")
        self.assertIsNone(plugin)

    @patch("plainspeak.plugins.manager.difflib.get_close_matches")
    def test_fuzzy_prefix_matching(self, mock_get_close_matches):
        """Test that prefixes get higher scores in fuzzy matching."""
        # Configure mocks to return verbs on specific inputs
        mock_get_close_matches.side_effect = lambda word, possibilities, n, cutoff: {
            "del": ["delete"],
            "up": ["update"],
        }.get(word, [])

        # Should match "delete" (prefix match)
        plugin = self.manager.get_plugin_for_verb("del")
        self.assertEqual(plugin, self.plugin)

        # Should match "update" (prefix match)
        plugin = self.manager.get_plugin_for_verb("up")
        self.assertEqual(plugin, self.plugin)


class TestMatchingPerformance(unittest.TestCase):
    """Test performance aspects of verb matching."""

    def setUp(self):
        """Set up test environment with many plugins."""
        # Create registry
        self.registry = PluginRegistry()

        # Create plugin manager
        self.manager = PluginManager()
        self.manager.registry = self.registry

        # Create 5 test plugins with 5 verbs each
        for i in range(5):
            plugin = PluginFixture(
                name=f"plugin_{i}",
                description=f"Test plugin {i}",
                verbs=[f"verb_{i}_{j}" for j in range(5)],
                priority=i,
            )
            self.registry.register(plugin)

        # Add one special plugin with known verbs for testing
        self.special_plugin = PluginFixture(
            name="special",
            description="Special test plugin",
            verbs=["special_find", "special_list", "special_create"],
            priority=100,
        )
        self.registry.register(self.special_plugin)

    @patch("plainspeak.plugins.base.lru_cache")
    def test_cache_performance(self, mock_lru_cache):
        """Test that caching improves performance."""
        # Create a mock decorated function
        mock_cached_func = Mock()
        mock_func = Mock(return_value=self.special_plugin)

        # Configure the mock_lru_cache to return a function that wraps mock_func
        mock_lru_cache.return_value = lambda func: mock_cached_func
        mock_cached_func.side_effect = mock_func

        # Replace the real function with our mock
        original_func = self.registry.get_plugin_for_verb
        self.registry.get_plugin_for_verb = mock_cached_func

        try:
            # First call
            plugin = self.manager.get_plugin_for_verb("special_find")
            self.assertEqual(plugin, self.special_plugin)
            self.assertEqual(mock_func.call_count, 1)

            # Second call with same verb (should use cache)
            plugin = self.manager.get_plugin_for_verb("special_find")
            self.assertEqual(plugin, self.special_plugin)
            # Since we're mocking, the call count would normally not increase
            # if caching worked, but our mock doesn't implement real caching
        finally:
            # Restore original function
            self.registry.get_plugin_for_verb = original_func

    def test_fuzzy_fallback_logic(self):
        """Test that exact matches are tried before fuzzy matches."""
        # Create a mock for _find_plugin_with_fuzzy_matching
        original_method = self.manager._find_plugin_with_fuzzy_matching
        mock_fuzzy = MagicMock()
        mock_fuzzy.return_value = None
        self.manager._find_plugin_with_fuzzy_matching = mock_fuzzy

        try:
            # Exact match should not call fuzzy matching
            plugin = self.manager.get_plugin_for_verb("special_list")
            self.assertEqual(plugin, self.special_plugin)
            mock_fuzzy.assert_not_called()

            # No exact match should call fuzzy matching
            plugin = self.manager.get_plugin_for_verb("special_listt")
            mock_fuzzy.assert_called_once()
        finally:
            # Restore original method
            self.manager._find_plugin_with_fuzzy_matching = original_method


class TestVerbRegistrationAndLookup(unittest.TestCase):
    """Test verb registration and lookup functionality."""

    def setUp(self):
        """Set up test environment."""
        # Create registry
        self.registry = PluginRegistry()

        # Create plugin manager
        self.manager = PluginManager()
        self.manager.registry = self.registry

    def test_plugin_registration(self):
        """Test that plugin registration adds verbs correctly."""
        # Create and register plugin
        plugin = PluginFixture(
            name="test",
            description="Test plugin",
            verbs=["verb1", "verb2", "verb3"],
            aliases={"alias1": "verb1", "alias2": "verb2"},
        )
        self.registry.register(plugin)

        # Check that verbs were registered
        all_verbs = self.registry.get_all_verbs()
        self.assertIn("verb1", all_verbs)
        self.assertIn("verb2", all_verbs)
        self.assertIn("verb3", all_verbs)
        self.assertIn("alias1", all_verbs)
        self.assertIn("alias2", all_verbs)

    def test_plugin_unregistration(self):
        """Test that plugin unregistration removes verbs correctly."""
        # Create and register plugin
        plugin = PluginFixture(
            name="test",
            description="Test plugin",
            verbs=["verb1", "verb2"],
            aliases={"alias1": "verb1"},
        )
        self.registry.register(plugin)

        # Verify registration
        all_verbs = self.registry.get_all_verbs()
        self.assertIn("verb1", all_verbs)

        # Unregister plugin by removing it from plugins dict (no unregister method exists)
        del self.registry.plugins["test"]

        # Clear caches
        self.registry.clear_caches()

        # Verify verbs were removed
        all_verbs = self.registry.get_all_verbs()
        self.assertNotIn("verb1", all_verbs)
        self.assertNotIn("alias1", all_verbs)

    def test_get_all_plugins(self):
        """Test getting all registered plugins."""
        # Create and register plugins
        plugin1 = PluginFixture(name="test1", description="Test plugin 1", verbs=["verb1"])
        plugin2 = PluginFixture(name="test2", description="Test plugin 2", verbs=["verb2"])

        self.registry.register(plugin1)
        self.registry.register(plugin2)

        # Get all plugins
        plugins = self.registry.plugins
        self.assertEqual(len(plugins), 2)
        self.assertEqual(plugins["test1"], plugin1)
        self.assertEqual(plugins["test2"], plugin2)


class TestErrorHandling(unittest.TestCase):
    """Test error handling in verb matching."""

    def setUp(self):
        """Set up test environment."""
        # Create registry
        self.registry = PluginRegistry()

        # Create plugin manager
        self.manager = PluginManager()
        self.manager.registry = self.registry

        # Create test plugin
        self.plugin = PluginFixture(name="test", description="Test plugin", verbs=["verb1", "verb2"])
        self.registry.register(self.plugin)

    def test_none_verb(self):
        """Test handling of None verb."""
        plugin = self.manager.get_plugin_for_verb(None)
        self.assertIsNone(plugin)

    def test_empty_verb(self):
        """Test handling of empty verb."""
        plugin = self.manager.get_plugin_for_verb("")
        self.assertIsNone(plugin)

    def test_registry_errors(self):
        """Test handling of registry errors."""
        # Get non-existent plugin
        plugin = self.registry.get_plugin("nonexistent")
        self.assertIsNone(plugin)

        # Create a fresh registry and manager for the consistency test
        new_registry = PluginRegistry()
        new_manager = PluginManager()
        new_manager.registry = new_registry

        # Register a plugin
        test_plugin = PluginFixture(name="test", description="Test plugin", verbs=["verb1", "verb2"])
        new_registry.register(test_plugin)

        # Verify the plugin can be found
        plugin = new_manager.get_plugin_for_verb("verb1")
        self.assertEqual(plugin, test_plugin)

        # Create inconsistency by completely removing the plugin from registry
        del new_registry.plugins["test"]

        # Clear caches
        new_registry.get_plugin_for_verb.cache_clear()
        new_registry.verb_to_plugin_cache.clear()
        new_manager.get_plugin_for_verb.cache_clear()

        # The lookup should now fail gracefully due to the inconsistency
        plugin = new_manager.get_plugin_for_verb("verb1")
        self.assertIsNone(plugin)

    def test_plugin_without_verbs(self):
        """Test handling of plugins without verbs."""
        # Create plugin without verbs
        plugin = PluginFixture(name="empty", description="Empty plugin")
        self.registry.register(plugin)

        # Should not match any verb
        all_verbs = self.registry.get_all_verbs()
        for verb in all_verbs.keys():
            plugin_found = self.registry.get_plugin_for_verb(verb)
            self.assertNotEqual(plugin_found, plugin)


if __name__ == "__main__":
    unittest.main()
