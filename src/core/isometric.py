"""
Isometric utilities for the RPG
"""

import math
import pygame

class IsometricRenderer:
    """Handles isometric rendering and coordinate conversion"""
    
    def __init__(self, tile_width=64, tile_height=32):
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.half_tile_width = tile_width // 2
        self.half_tile_height = tile_height // 2
    
    def cart_to_iso(self, cart_x, cart_y):
        """Convert Cartesian coordinates to isometric screen coordinates"""
        # Use proper isometric conversion as described in the articles
        # This creates the diamond-shaped grid with correct 2:1 ratio
        iso_x = (cart_x - cart_y) * self.half_tile_width
        iso_y = (cart_x + cart_y) * self.half_tile_height
        return iso_x, iso_y
    
    def iso_to_cart(self, iso_x, iso_y):
        """Convert isometric screen coordinates to Cartesian coordinates"""
        # Inverse of cart_to_iso conversion
        # From: iso_x = (cart_x - cart_y) * half_tile_width
        #       iso_y = (cart_x + cart_y) * half_tile_height
        # Solve for cart_x and cart_y:
        cart_x = (iso_x / self.half_tile_width + iso_y / self.half_tile_height) / 2
        cart_y = (iso_y / self.half_tile_height - iso_x / self.half_tile_width) / 2
        return cart_x, cart_y
    
    def world_to_screen(self, world_x, world_y, camera_x=0, camera_y=0):
        """Convert world coordinates to screen coordinates"""
        iso_x, iso_y = self.cart_to_iso(world_x, world_y)
        screen_x = iso_x - camera_x
        screen_y = iso_y - camera_y
        return screen_x, screen_y
    
    def screen_to_world(self, screen_x, screen_y, camera_x=0, camera_y=0):
        """Convert screen coordinates to world coordinates"""
        iso_x = screen_x + camera_x
        iso_y = screen_y + camera_y
        world_x, world_y = self.iso_to_cart(iso_x, iso_y)
        return world_x, world_y
    
    def create_diamond_tile(self, color, size=None):
        """Create a diamond-shaped tile sprite"""
        if size is None:
            width, height = self.tile_width, self.tile_height
        else:
            width, height = size, size // 2
            
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Create diamond shape
        points = [
            (width // 2, 0),           # Top
            (width, height // 2),       # Right
            (width // 2, height),       # Bottom
            (0, height // 2)           # Left
        ]
        
        pygame.draw.polygon(surface, color, points)
        
        # Add border
        pygame.draw.polygon(surface, (0, 0, 0), points, 2)
        
        return surface
    
    def create_cube_tile(self, top_color, left_color, right_color, size=None):
        """Create a 3D cube-like tile sprite with proper isometric proportions"""
        if size is None:
            width, height = self.tile_width, self.tile_height
        else:
            width, height = size, size // 2
            
        # Create taller surface for wall sprites
        wall_height = height * 2  # Make walls twice as tall
        surface = pygame.Surface((width, wall_height), pygame.SRCALPHA)
        
        # Top face (diamond) - positioned at the top of the wall
        top_points = [
            (width // 2, 0),
            (width, height // 2),
            (width // 2, height),
            (0, height // 2)
        ]
        pygame.draw.polygon(surface, top_color, top_points)
        
        # Left face - extends down from the diamond
        left_points = [
            (0, height // 2),
            (width // 2, height),
            (width // 2, wall_height),
            (0, wall_height - height // 2)
        ]
        pygame.draw.polygon(surface, left_color, left_points)
        
        # Right face - extends down from the diamond
        right_points = [
            (width // 2, height),
            (width, height // 2),
            (width, wall_height - height // 2),
            (width // 2, wall_height)
        ]
        pygame.draw.polygon(surface, right_color, right_points)
        
        # Add borders for better definition
        pygame.draw.polygon(surface, (0, 0, 0), top_points, 2)
        pygame.draw.polygon(surface, (0, 0, 0), left_points, 2)
        pygame.draw.polygon(surface, (0, 0, 0), right_points, 2)
        
        return surface

def sort_by_depth(objects):
    """Sort objects by their depth for proper isometric rendering with occlusion"""
    def get_sort_key(obj):
        # Base depth calculation
        base_depth = obj.x + obj.y
        
        # Adjust depth based on entity type for proper layering
        if hasattr(obj, 'entity_type'):
            if obj.entity_type == "object" and ("Tree" in obj.name or "Wall" in obj.name):
                # Trees and walls should render after other entities at the same position
                # to provide proper occlusion
                return base_depth + 0.5
        
        return base_depth
    
    return sorted(objects, key=get_sort_key)