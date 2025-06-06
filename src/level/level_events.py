"""
Event handling and input processing
"""

import pygame


class EventHandlingMixin:
    """Mixin class for event handling functionality"""
    
    def handle_event(self, event):
        """Handle level events"""
        # Check if dialogue window is open and handle its events first
        if self.player.current_dialogue and self.player.current_dialogue.show:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.player.current_dialogue.handle_click(event.pos):
                    return  # Dialogue consumed the event
        
        # Check if AI chat window is open and handle its events first
        if hasattr(self.player, 'current_ai_chat') and self.player.current_ai_chat and self.player.current_ai_chat.is_active:
            # Handle AI chat input
            if event.type == pygame.KEYDOWN:
                message = self.player.current_ai_chat.handle_input(event)
                if message:
                    print(f"🔧 [EventHandling] Player sent message: '{message}'")
                    # Find the NPC that owns this chat and send the message
                    for npc in self.npcs:
                        if hasattr(npc, 'chat_window') and npc.chat_window == self.player.current_ai_chat:
                            print(f"🔧 [EventHandling] Found NPC {npc.name}, sending message to AI")
                            npc.chat_window.add_message("Player", message)
                            # Get AI response
                            if npc.game_context:
                                context = npc.game_context.get_context()
                                ai_response = npc.ai_integration.send_message(message, context)
                                npc.chat_window.add_message(npc.name, ai_response)
                                print(f"🔧 [EventHandling] AI responded: '{ai_response}'")
                            break
                return  # AI chat consumed the event
        
        # Check if any shop is open and handle shop events
        for npc in self.npcs:
            if hasattr(npc, 'shop') and npc.shop and npc.shop.show:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if npc.shop.handle_click(event.pos, self.player):
                        return  # Shop consumed the event
        
        # Check if player's current shop is open (from MCP system)
        if hasattr(self.player, 'current_shop') and self.player.current_shop and self.player.current_shop.show:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.player.current_shop.handle_click(event.pos, self.player):
                    return  # Shop consumed the event
        
        # Handle mouse clicks for interaction and movement
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self.handle_click(event.pos)
            elif event.button == 3:  # Right click
                self.handle_right_click(event.pos)
            elif event.button == 4:  # Mouse wheel up
                # Scroll up in game log
                if hasattr(self, 'game') and hasattr(self.game, 'game_log'):
                    if self.game.game_log.handle_scroll(1):  # Scroll up
                        pass  # Successfully scrolled
                elif hasattr(self, 'player') and hasattr(self.player, 'game_log'):
                    if self.player.game_log.handle_scroll(1):  # Scroll up
                        pass  # Successfully scrolled
            elif event.button == 5:  # Mouse wheel down
                # Scroll down in game log
                if hasattr(self, 'game') and hasattr(self.game, 'game_log'):
                    if self.game.game_log.handle_scroll(-1):  # Scroll down
                        pass  # Successfully scrolled
                elif hasattr(self, 'player') and hasattr(self.player, 'game_log'):
                    if self.player.game_log.handle_scroll(-1):  # Scroll down
                        pass  # Successfully scrolled
        
        # Handle mouse motion for cursor changes
        elif event.type == pygame.MOUSEMOTION:
            self.handle_mouse_hover(event.pos)
    
    def handle_mouse_hover(self, pos):
        """Handle mouse hover for cursor changes"""
        # Only handle hover in mouse mode
        if (hasattr(self.player, 'movement_system') and 
            self.player.movement_system.movement_mode == "mouse"):
            # Convert screen position to world position
            world_x, world_y = self.iso_renderer.screen_to_world(pos[0], pos[1], self.camera_x, self.camera_y)
            
            # Let the movement system handle hover
            self.player.movement_system.handle_mouse_hover(world_x, world_y, self)
    
    def handle_click(self, pos):
        """Handle mouse click at position"""
        # Check if clicking on game log scroll arrows first
        if hasattr(self, 'game') and hasattr(self.game, 'game_log'):
            if self.game.game_log.handle_click(pos):
                return  # Game log consumed the click
        elif hasattr(self, 'player') and hasattr(self.player, 'game_log'):
            if self.player.game_log.handle_click(pos):
                return  # Game log consumed the click
        
        # Check if clicking on inventory button
        if hasattr(self, 'inventory_button_rect') and self.inventory_button_rect.collidepoint(pos):
            # Toggle inventory
            self.player.inventory.show = not self.player.inventory.show
            if self.player.game_log:
                if self.player.inventory.show:
                    self.player.game_log.add_message("Inventory opened", "system")
                else:
                    self.player.game_log.add_message("Inventory closed", "system")
            return
        
        # Only handle movement clicks in mouse mode
        if (hasattr(self.player, 'movement_system') and 
            self.player.movement_system.movement_mode == "mouse"):
            # Convert screen position to world position
            world_x, world_y = self.iso_renderer.screen_to_world(pos[0], pos[1], self.camera_x, self.camera_y)
            
            # Let the player handle the click
            self.player.handle_mouse_click(world_x, world_y, self)
        elif (hasattr(self.player, 'movement_system') and 
              self.player.movement_system.movement_mode == "wasd"):
            # In WASD mode, clicks can still be used for interaction (but not movement)
            world_x, world_y = self.iso_renderer.screen_to_world(pos[0], pos[1], self.camera_x, self.camera_y)
            self._handle_wasd_click_interaction(world_x, world_y)
    
    def handle_right_click(self, pos):
        """Handle right mouse click for context actions"""
        # Convert screen position to world position
        world_x, world_y = self.iso_renderer.screen_to_world(pos[0], pos[1], self.camera_x, self.camera_y)
        
        # Check what was right-clicked
        clicked_entity = None
        
        # Check enemies for info
        for enemy in self.enemies:
            if abs(world_x - enemy.x) < 1.2 and abs(world_y - enemy.y) < 1.2:
                if self.player.game_log:
                    self.player.game_log.add_message(f"{enemy.name}: Health {enemy.health}/{enemy.max_health}, Damage {enemy.damage}", "system")
                clicked_entity = enemy
                break
        
        # Check NPCs for info (only if visible and interactive)
        if not clicked_entity:
            for npc in self.npcs:
                if abs(world_x - npc.x) < 1.2 and abs(world_y - npc.y) < 1.2:
                    # Check if NPC is visible (not hidden by building roof)
                    if not self._is_npc_visible_for_interaction(npc):
                        continue  # Skip hidden NPCs
                    
                    # Allow inspection of background NPCs, but show different info
                    if hasattr(npc, 'is_background') and npc.is_background:
                        if self.player.game_log:
                            # Show basic info for background NPCs
                            self.player.game_log.add_message(f"{npc.name} (Background NPC)", "system")
                        clicked_entity = npc
                        break
                    
                    if self.player.game_log:
                        # Just show NPC info on right-click, not dialog
                        npc_info = f"{npc.name}"
                        if npc.has_shop:
                            npc_info += " (Shopkeeper)"
                        self.player.game_log.add_message(npc_info, "system")
                    clicked_entity = npc
                    break
        
        # Check chests for info
        if not clicked_entity:
            for chest in self.chests:
                if abs(world_x - chest.x) < 1.2 and abs(world_y - chest.y) < 1.2:
                    if self.player.game_log:
                        status = "Empty" if chest.is_opened else "Unopened"
                        chest_info = f"{chest.name} ({status})"
                        if not chest.is_opened:
                            chest_info += f" - {len(chest.loot_items)} items inside"
                        self.player.game_log.add_message(chest_info, "system")
                    clicked_entity = chest
                    break
        
        # Check items for info
        if not clicked_entity:
            for item in self.items:
                if abs(world_x - item.x) < 1.2 and abs(world_y - item.y) < 1.2:
                    effect_str = ", ".join([f"{k}: {v}" for k, v in item.effect.items()])
                    if self.player.game_log:
                        self.player.game_log.add_message(f"{item.name} ({item.item_type}): {effect_str}", "item")
                    clicked_entity = item
                    break
        
        if not clicked_entity:
            # Show tile info
            tile_x = int(world_x)
            tile_y = int(world_y)
            if 0 <= tile_x < self.width and 0 <= tile_y < self.height:
                tile_names = {
                    self.TILE_GRASS: "Grass",
                    self.TILE_DIRT: "Dirt",
                    self.TILE_STONE: "Stone Path",
                    self.TILE_WATER: "Water",
                    self.TILE_WALL: "Wall",
                    self.TILE_DOOR: "Door",
                    self.TILE_BRICK: "Brick Floor",
                    self.TILE_SAND: "Sand",
                    self.TILE_SNOW: "Snow",
                    self.TILE_FOREST_FLOOR: "Forest Floor",
                    self.TILE_SWAMP: "Swamp"
                }
                tile_type = self.get_tile(tile_x, tile_y) if hasattr(self, 'get_tile') else self.tiles[tile_y][tile_x]
                tile_name = tile_names.get(tile_type, "Unknown")
                walkable_value = self.walkable[tile_y][tile_x]
                if walkable_value <= 0:
                    walkable = "blocked"
                elif walkable_value < 1:
                    walkable = f"restricted ({walkable_value:.1f})"
                else:
                    walkable = "walkable"
                if self.player.game_log:
                    self.player.game_log.add_message(f"Tile ({tile_x}, {tile_y}): {tile_name} ({walkable})", "system")
    
    def _handle_wasd_click_interaction(self, world_x, world_y):
        """Handle click interactions in WASD mode (no movement, just interaction)"""
        import math
        
        # Check if clicking on an entity for interaction (no movement)
        clicked_entity = None
        
        # Check NPCs (must be within interaction range AND visible AND interactive)
        for npc in self.npcs:
            if abs(world_x - npc.x) < 1.2 and abs(world_y - npc.y) < 1.2:
                # Check if NPC is visible (not hidden by building roof)
                if not self._is_npc_visible_for_interaction(npc):
                    continue  # Skip hidden NPCs
                
                # Handle background NPCs differently
                if hasattr(npc, 'is_background') and npc.is_background:
                    # Background NPCs give minimal response
                    if self.player.game_log:
                        responses = [
                            f"{npc.name} nods briefly.",
                            f"{npc.name} looks busy.",
                            f"{npc.name} gives a polite wave.",
                            f"{npc.name} is going about their day."
                        ]
                        import random
                        response = random.choice(responses)
                        self.player.game_log.add_message(response, "dialog")
                    return  # Don't allow full interaction
                
                dist = math.sqrt((self.player.x - npc.x)**2 + (self.player.y - npc.y)**2)
                if dist < 2.0:  # Only interact if close enough
                    clicked_entity = npc
                    break
                else:
                    if self.player.game_log:
                        self.player.game_log.add_message(f"Too far from {npc.name}! Walk closer.", "system")
                    return
        
        # Check chests (must be within interaction range)
        if not clicked_entity:
            for chest in self.chests:
                if abs(world_x - chest.x) < 1.2 and abs(world_y - chest.y) < 1.2:
                    dist = math.sqrt((self.player.x - chest.x)**2 + (self.player.y - chest.y)**2)
                    if dist < 1.5:  # Must be right next to chest
                        clicked_entity = chest
                        break
                    else:
                        if self.player.game_log:
                            self.player.game_log.add_message(f"Too far from {chest.name}! Walk closer.", "system")
                        return
        
        # Check items (must be within pickup range)
        if not clicked_entity:
            for item in self.items[:]:
                if abs(world_x - item.x) < 1.2 and abs(world_y - item.y) < 1.2:
                    dist = math.sqrt((self.player.x - item.x)**2 + (self.player.y - item.y)**2)
                    if dist < 2.0:
                        # Get audio manager
                        audio = getattr(self.player.asset_loader, 'audio_manager', None) if self.player.asset_loader else None
                        
                        if self.player.add_item(item):
                            self.items.remove(item)
                            # Play pickup sound based on item type
                            if audio:
                                if item.name.lower().find('gold') != -1 or item.name.lower().find('coin') != -1:
                                    audio.play_ui_sound("coin")
                                elif item.item_type == "consumable":
                                    audio.play_sound("ui", "leather_item")
                                else:
                                    audio.play_ui_sound("click")
                            if self.player.game_log:
                                self.player.game_log.add_message(f"Picked up {item.name}", "item")
                        else:
                            if self.player.game_log:
                                self.player.game_log.add_message("Inventory is full!", "system")
                    else:
                        if self.player.game_log:
                            self.player.game_log.add_message(f"Too far from {item.name}! Walk closer.", "system")
                    return
        
        # Check enemies for attack (must be within attack range)
        if not clicked_entity:
            for enemy in self.enemies:
                dx = world_x - enemy.x
                dy = world_y - enemy.y
                click_distance = math.sqrt(dx * dx + dy * dy)
                
                if click_distance < 1.0:
                    player_dist = math.sqrt((self.player.x - enemy.x)**2 + (self.player.y - enemy.y)**2)
                    if player_dist <= self.player.combat_system.attack_range:
                        # Update player direction to face the enemy
                        enemy_dx = enemy.x - self.player.x
                        enemy_dy = enemy.y - self.player.y
                        if abs(enemy_dx) > abs(enemy_dy):
                            self.player.movement_system.direction = 3 if enemy_dx > 0 else 1
                        else:
                            self.player.movement_system.direction = 0 if enemy_dy > 0 else 2
                        
                        # Attack if have stamina
                        stamina_cost = self.player.combat_system.get_weapon_stamina_cost()
                        if self.player.stamina >= stamina_cost:
                            self.player.combat_system.attack([enemy], self)
                            if self.player.game_log:
                                self.player.game_log.add_message(f"Attacking {enemy.name}!", "combat")
                        else:
                            if self.player.game_log:
                                weapon_name = self.player.equipped_weapon.name if self.player.equipped_weapon else "fists"
                                self.player.game_log.add_message(f"Not enough stamina to attack with {weapon_name}! (Need {stamina_cost})", "combat")
                    else:
                        if self.player.game_log:
                            self.player.game_log.add_message(f"Too far from {enemy.name}! Walk closer to attack.", "combat")
                    return
        
        # Interact with clicked entity
        if clicked_entity and hasattr(clicked_entity, 'interact'):
            clicked_entity.interact(self.player)
    
    def _is_npc_visible_for_interaction(self, npc):
        """
        Check if NPC is visible for interaction (not hidden by building roof)
        Uses the same logic as the rendering system
        """
        npc_x, npc_y = int(npc.x), int(npc.y)
        player_x, player_y = int(self.player.x), int(self.player.y)
        
        # Check if NPC is inside a building
        if hasattr(self, 'get_tile'):
            npc_tile_type = self.get_tile(npc_x, npc_y)
        else:
            if 0 <= npc_y < len(self.tiles) and 0 <= npc_x < len(self.tiles[0]):
                npc_tile_type = self.tiles[npc_y][npc_x]
            else:
                return True  # Default to visible if we can't check
        
        # Check if NPC is on a building tile (interior floor or wall)
        is_npc_in_building = (npc_tile_type == self.TILE_BRICK or 
                             (hasattr(self, 'wall_renderer') and 
                              self.wall_renderer.is_wall_tile(npc_tile_type)) or
                             npc_tile_type == self.TILE_DOOR)
        
        if is_npc_in_building:
            # NPC is inside a building - check if player is close to this building
            npc_building_bounds = self.get_building_bounds_at(npc_x, npc_y)
            if npc_building_bounds:
                min_x, min_y, max_x, max_y = npc_building_bounds
                
                # Check if player is within 0.75 tiles of the building bounds (same as rendering logic)
                expanded_min_x = min_x - 0.75
                expanded_max_x = max_x + 0.75
                expanded_min_y = min_y - 0.75
                expanded_max_y = max_y + 0.75
                
                # NPC is visible if player is close to the building
                return (expanded_min_x <= player_x <= expanded_max_x and 
                        expanded_min_y <= player_y <= expanded_max_y)
        
        # NPC is not in a building, so it's always visible
        return True