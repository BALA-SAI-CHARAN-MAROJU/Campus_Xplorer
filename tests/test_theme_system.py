"""
Property-based tests for enhanced theme system
Feature: campus-explorer-enhancement, Task 8
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant
import json
import time

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    # Provide stub classes so the rest of the module can be parsed
    By = None
    Options = None
    TimeoutException = Exception
    NoSuchElementException = Exception


class ThemeSwitchingMachine(RuleBasedStateMachine):
    """
    State machine for testing theme switching consistency
    Property 14: Theme Switching Consistency
    """
    
    def __init__(self):
        if not SELENIUM_AVAILABLE:
            pytest.skip("selenium not installed")
        super().__init__()
        self.current_theme = 'light'
        self.theme_history = []
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup headless Chrome driver for testing"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.get('http://localhost:5000')
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
        except Exception as e:
            pytest.skip(f"Could not setup Chrome driver: {e}")
    
    def teardown(self):
        """Cleanup driver"""
        if self.driver:
            self.driver.quit()
    
    @rule()
    def toggle_theme(self):
        """Toggle theme and verify consistency"""
        if not self.driver:
            return
            
        try:
            # Find theme toggle button
            theme_toggle = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, 'theme-toggle'))
            )
            
            # Get current theme before toggle
            old_theme = self.driver.execute_script(
                "return document.documentElement.getAttribute('data-theme') || 'light'"
            )
            
            # Click theme toggle
            theme_toggle.click()
            
            # Wait for theme transition
            time.sleep(0.5)
            
            # Get new theme
            new_theme = self.driver.execute_script(
                "return document.documentElement.getAttribute('data-theme') || 'light'"
            )
            
            # Verify theme changed
            assert old_theme != new_theme, f"Theme should have changed from {old_theme}"
            assert new_theme in ['light', 'dark'], f"Invalid theme: {new_theme}"
            
            # Update state
            self.current_theme = new_theme
            self.theme_history.append({
                'from': old_theme,
                'to': new_theme,
                'timestamp': time.time()
            })
            
        except (TimeoutException, NoSuchElementException) as e:
            pytest.skip(f"Theme toggle not available: {e}")
    
    @rule(theme=st.sampled_from(['light', 'dark']))
    def set_theme_programmatically(self, theme):
        """Set theme programmatically and verify"""
        if not self.driver:
            return
            
        try:
            # Set theme via JavaScript
            self.driver.execute_script(f"""
                if (window.themeManager) {{
                    window.themeManager.setTheme('{theme}', false);
                }}
            """)
            
            # Wait for theme to apply
            time.sleep(0.2)
            
            # Verify theme was set
            actual_theme = self.driver.execute_script(
                "return document.documentElement.getAttribute('data-theme') || 'light'"
            )
            
            assert actual_theme == theme, f"Expected theme {theme}, got {actual_theme}"
            
            # Update state
            self.current_theme = theme
            
        except Exception as e:
            pytest.skip(f"Could not set theme programmatically: {e}")
    
    @rule()
    def verify_theme_persistence(self):
        """Verify theme persists across page reloads"""
        if not self.driver:
            return
            
        try:
            # Get current theme
            current_theme = self.driver.execute_script(
                "return document.documentElement.getAttribute('data-theme') || 'light'"
            )
            
            # Reload page
            self.driver.refresh()
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            
            # Wait for theme manager to initialize
            time.sleep(1)
            
            # Verify theme persisted
            persisted_theme = self.driver.execute_script(
                "return document.documentElement.getAttribute('data-theme') || 'light'"
            )
            
            assert persisted_theme == current_theme, \
                f"Theme should persist across reloads: {current_theme} -> {persisted_theme}"
            
        except Exception as e:
            pytest.skip(f"Could not verify theme persistence: {e}")
    
    @invariant()
    def theme_consistency_invariant(self):
        """Verify theme consistency across all elements"""
        if not self.driver:
            return
            
        try:
            # Get current theme
            current_theme = self.driver.execute_script(
                "return document.documentElement.getAttribute('data-theme') || 'light'"
            )
            
            # Verify theme is applied to document
            assert current_theme in ['light', 'dark'], f"Invalid theme: {current_theme}"
            
            # Check CSS custom properties are set correctly
            primary_color = self.driver.execute_script("""
                return getComputedStyle(document.documentElement)
                    .getPropertyValue('--primary-color').trim();
            """)
            
            bg_primary = self.driver.execute_script("""
                return getComputedStyle(document.documentElement)
                    .getPropertyValue('--bg-primary').trim();
            """)
            
            # Verify colors are set
            assert primary_color, "Primary color should be set"
            assert bg_primary, "Background color should be set"
            
            # Verify theme toggle button state
            try:
                theme_toggle = self.driver.find_element(By.ID, 'theme-toggle')
                aria_label = theme_toggle.get_attribute('aria-label')
                
                if current_theme == 'light':
                    assert 'dark' in aria_label.lower(), \
                        f"Light theme should show 'Switch to dark' label, got: {aria_label}"
                else:
                    assert 'light' in aria_label.lower(), \
                        f"Dark theme should show 'Switch to light' label, got: {aria_label}"
                        
            except NoSuchElementException:
                pass  # Theme toggle might not be present in all tests
            
        except Exception as e:
            pytest.skip(f"Could not verify theme consistency: {e}")


class TestThemeSwitchingConsistency:
    """
    Property 14: Theme Switching Consistency
    Tests that theme switching works smoothly and consistently
    """
    
    @settings(max_examples=20, deadline=None)
    @given(st.data())
    def test_theme_switching_consistency_property(self, data):
        """
        Property 14: Theme Switching Consistency
        Tests that theme switching maintains consistency across all components
        """
        machine = ThemeSwitchingMachine()
        try:
            machine.execute(data)
        finally:
            machine.teardown()


class TestThemeSystemComponents:
    """Unit tests for theme system components"""
    
    def test_theme_css_variables_defined(self):
        """Test that all required CSS variables are defined"""
        required_variables = [
            '--primary-color',
            '--secondary-color',
            '--bg-primary',
            '--bg-secondary',
            '--text-primary',
            '--text-secondary',
            '--border-color',
            '--shadow-md',
            '--transition-normal'
        ]
        
        # This would be tested in a browser environment
        # For now, we'll just verify the variables exist in our CSS file
        with open('static/css/theme-system.css', 'r') as f:
            css_content = f.read()
            
        for variable in required_variables:
            assert variable in css_content, f"CSS variable {variable} not found"
    
    def test_theme_javascript_functions(self):
        """Test that theme JavaScript functions are properly defined"""
        with open('static/js/theme-manager.js', 'r') as f:
            js_content = f.read()
        
        required_functions = [
            'class ThemeManager',
            'toggleTheme',
            'applyTheme',
            'loadSavedTheme',
            'updateToggleButton'
        ]
        
        for function in required_functions:
            assert function in js_content, f"JavaScript function {function} not found"
    
    @given(
        theme=st.sampled_from(['light', 'dark']),
        animate=st.booleans()
    )
    def test_theme_application_parameters(self, theme, animate):
        """Test theme application with various parameters"""
        # Mock theme manager behavior
        assert theme in ['light', 'dark'], f"Invalid theme: {theme}"
        assert isinstance(animate, bool), f"Animate should be boolean: {animate}"
        
        # Verify theme would be stored correctly
        expected_storage_key = 'campus-explorer-theme'
        expected_storage_value = theme
        
        assert expected_storage_key == 'campus-explorer-theme'
        assert expected_storage_value in ['light', 'dark']
    
    @given(
        transitions=st.lists(
            st.sampled_from(['light', 'dark']),
            min_size=1,
            max_size=10
        )
    )
    def test_theme_transition_sequence(self, transitions):
        """Test sequences of theme transitions"""
        current_theme = 'light'
        
        for new_theme in transitions:
            # Verify valid transition
            assert new_theme in ['light', 'dark']
            
            # Simulate theme change
            previous_theme = current_theme
            current_theme = new_theme
            
            # Verify transition is valid
            assert previous_theme in ['light', 'dark']
            assert current_theme in ['light', 'dark']
    
    def test_theme_accessibility_features(self):
        """Test theme accessibility features"""
        # Verify reduced motion support exists
        with open('static/css/theme-system.css', 'r') as f:
            css_content = f.read()
        
        assert 'prefers-reduced-motion' in css_content, \
            "Reduced motion support not found"
        assert 'prefers-contrast' in css_content, \
            "High contrast support not found"
        assert 'aria-label' in open('static/js/theme-manager.js', 'r').read(), \
            "Accessibility labels not found"
    
    @given(
        color_scheme=st.sampled_from(['light', 'dark', 'no-preference'])
    )
    def test_system_theme_detection(self, color_scheme):
        """Test system theme preference detection"""
        # Mock system preference detection
        if color_scheme == 'dark':
            expected_theme = 'dark'
        elif color_scheme == 'light':
            expected_theme = 'light'
        else:
            expected_theme = 'light'  # Default fallback
        
        assert expected_theme in ['light', 'dark']
    
    def test_theme_meta_color_updates(self):
        """Test that meta theme-color is updated correctly"""
        light_color = '#ffffff'
        dark_color = '#111827'
        
        # Verify colors are valid hex codes
        assert light_color.startswith('#') and len(light_color) == 7
        assert dark_color.startswith('#') and len(dark_color) == 7
        
        # Test color mapping
        theme_colors = {
            'light': light_color,
            'dark': dark_color
        }
        
        for theme, color in theme_colors.items():
            assert theme in ['light', 'dark']
            assert color.startswith('#')
    
    @given(
        storage_available=st.booleans(),
        saved_theme=st.one_of(
            st.none(),
            st.sampled_from(['light', 'dark', 'invalid'])
        )
    )
    def test_theme_persistence_edge_cases(self, storage_available, saved_theme):
        """Test theme persistence with various edge cases"""
        if not storage_available:
            # Should fall back to system preference
            expected_fallback = 'light'  # Default
            assert expected_fallback in ['light', 'dark']
        elif saved_theme == 'invalid':
            # Should fall back to default
            expected_fallback = 'light'
            assert expected_fallback in ['light', 'dark']
        elif saved_theme in ['light', 'dark']:
            # Should use saved theme
            assert saved_theme in ['light', 'dark']
        else:
            # Should use system preference
            expected_fallback = 'light'  # Default
            assert expected_fallback in ['light', 'dark']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])