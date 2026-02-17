"""
Oblique projection coordinate utilities for Snake3D.

This module provides simple grid-to-screen coordinate conversion for
a Stardew Valley-style 3/4 top-down view. Unlike true isometric projection,
this uses square tiles with depth shown through vertical offset.

Visual representation:
    ┌───┐  <- top face (lighter color)
    ├───┤  <- front face (darker color, shows depth)
    └───┘
"""


def grid_to_screen(grid_x, grid_y, cell_size, origin_x=0, origin_y=0):
    """
    Convert grid coordinates to screen coordinates.
    
    Simple multiplication - no complex isometric math needed.
    
    Args:
        grid_x: X position in grid coordinates
        grid_y: Y position in grid coordinates
        cell_size: Size of each cell in pixels
        origin_x: Screen X offset (for play area positioning)
        origin_y: Screen Y offset (for HUD offset)
        
    Returns:
        Tuple (screen_x, screen_y) for the top-left of the tile
    """
    screen_x = origin_x + grid_x * cell_size
    screen_y = origin_y + grid_y * cell_size
    return (screen_x, screen_y)


def screen_to_grid(screen_x, screen_y, cell_size, origin_x=0, origin_y=0):
    """
    Convert screen coordinates back to grid coordinates.
    
    Args:
        screen_x: X position on screen
        screen_y: Y position on screen
        cell_size: Size of each cell in pixels
        origin_x: Screen X offset
        origin_y: Screen Y offset
        
    Returns:
        Tuple (grid_x, grid_y) as integers
    """
    grid_x = (screen_x - origin_x) // cell_size
    grid_y = (screen_y - origin_y) // cell_size
    return (grid_x, grid_y)


def get_depth(grid_x, grid_y):
    """
    Calculate depth value for sorting (draw order).
    
    In oblique view, objects with higher Y should be drawn later (in front).
    For same Y, higher X is drawn later.
    
    Args:
        grid_x: X position in grid
        grid_y: Y position in grid
        
    Returns:
        Depth value (higher = drawn later/in front)
    """
    return grid_y * 1000 + grid_x


def sort_by_depth(items, key_func=None):
    """
    Sort items by their depth for proper draw order.
    
    Args:
        items: List of items to sort
        key_func: Function that takes an item and returns (grid_x, grid_y)
                  If None, items are assumed to be (x, y) tuples
                  
    Returns:
        List sorted by depth (back to front)
    """
    if key_func is None:
        key_func = lambda item: item
    
    return sorted(items, key=lambda item: get_depth(*key_func(item)))


def calculate_window_size(grid_width, grid_height, cell_size, depth_height,
                          padding=10, hud_width=150, hud_top=55):
    """
    Calculate the window size needed for the oblique grid.
    
    Much simpler than isometric - just grid dimensions * cell size.
    
    Args:
        grid_width: Number of cells in X direction
        grid_height: Number of cells in Y direction
        cell_size: Size of each cell in pixels
        depth_height: Height of depth/front face in pixels
        padding: Extra padding around the grid
        hud_width: Width of side HUD panel
        hud_top: Height of top HUD bar
        
    Returns:
        Tuple (window_width, window_height, origin_x, origin_y)
    """
    # Play area size
    play_width = grid_width * cell_size
    play_height = grid_height * cell_size + depth_height  # Extra for bottom row depth
    
    # Total window size
    window_width = play_width + padding * 2 + hud_width
    window_height = play_height + padding * 2 + hud_top
    
    # Origin point (where grid[0,0] would be placed)
    origin_x = padding
    origin_y = padding + hud_top
    
    return (window_width, window_height, origin_x, origin_y)


def get_tile_rect(grid_x, grid_y, cell_size, origin_x=0, origin_y=0):
    """
    Get the rectangle for a tile's top face.
    
    Args:
        grid_x, grid_y: Grid position
        cell_size: Size of each cell
        origin_x, origin_y: Screen origin offset
        
    Returns:
        Tuple (x, y, width, height) for the tile rectangle
    """
    screen_x, screen_y = grid_to_screen(grid_x, grid_y, cell_size, origin_x, origin_y)
    return (screen_x, screen_y, cell_size, cell_size)


def get_cube_rects(grid_x, grid_y, cell_size, depth_height, origin_x=0, origin_y=0):
    """
    Get rectangles for drawing a cube (top face + front face).
    
    Args:
        grid_x, grid_y: Grid position
        cell_size: Size of each cell
        depth_height: Height of the front/depth face
        origin_x, origin_y: Screen origin offset
        
    Returns:
        Dict with 'top' and 'front' keys, each containing (x, y, width, height)
    """
    screen_x, screen_y = grid_to_screen(grid_x, grid_y, cell_size, origin_x, origin_y)
    
    return {
        'top': (screen_x, screen_y, cell_size, cell_size),
        'front': (screen_x, screen_y + cell_size, cell_size, depth_height)
    }
