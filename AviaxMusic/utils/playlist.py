import asyncio
import json
import os
import random
from typing import Dict, List, Union

class PlaylistManager:
    """Manager for handling user playlists and recommendations"""
    
    def __init__(self):
        self.playlists_dir = "playlists"
        self.user_history = {}
        self.ensure_playlist_dir()
    
    def ensure_playlist_dir(self):
        """Ensure the playlists directory exists"""
        if not os.path.exists(self.playlists_dir):
            os.makedirs(self.playlists_dir)
            
    async def save_user_playlist(self, user_id: int, playlist_name: str, tracks: List[Dict]):
        """Save a user's playlist to file"""
        try:
            user_dir = os.path.join(self.playlists_dir, str(user_id))
            if not os.path.exists(user_dir):
                os.makedirs(user_dir)
                
            playlist_file = os.path.join(user_dir, f"{playlist_name}.json")
            
            with open(playlist_file, 'w', encoding='utf-8') as f:
                json.dump(tracks, f, indent=4)
                
            return True, playlist_file
        except Exception as e:
            print(f"Error saving playlist: {e}")
            return False, str(e)
    
    async def get_user_playlists(self, user_id: int) -> List[str]:
        """Get list of playlists for a user"""
        user_dir = os.path.join(self.playlists_dir, str(user_id))
        if not os.path.exists(user_dir):
            return []
            
        playlists = []
        for file in os.listdir(user_dir):
            if file.endswith('.json'):
                playlists.append(file[:-5])  # Remove .json extension
                
        return playlists
    
    async def get_playlist_tracks(self, user_id: int, playlist_name: str) -> List[Dict]:
        """Get tracks from a playlist"""
        playlist_file = os.path.join(self.playlists_dir, str(user_id), f"{playlist_name}.json")
        if not os.path.exists(playlist_file):
            return []
            
        try:
            with open(playlist_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading playlist: {e}")
            return []
    
    async def add_to_playlist(self, user_id: int, playlist_name: str, track: Dict) -> bool:
        """Add a track to a playlist"""
        try:
            # Get existing tracks
            tracks = await self.get_playlist_tracks(user_id, playlist_name)
            
            # Check if track already exists in playlist
            track_id = track.get('videoid')
            if any(t.get('videoid') == track_id for t in tracks):
                return False  # Track already exists
                
            # Add track to playlist
            tracks.append(track)
            
            # Save updated playlist
            success, _ = await self.save_user_playlist(user_id, playlist_name, tracks)
            return success
        except Exception as e:
            print(f"Error adding to playlist: {e}")
            return False
    
    async def remove_from_playlist(self, user_id: int, playlist_name: str, track_id: str) -> bool:
        """Remove a track from a playlist"""
        try:
            # Get existing tracks
            tracks = await self.get_playlist_tracks(user_id, playlist_name)
            
            # Filter out the track to be removed
            updated_tracks = [t for t in tracks if t.get('videoid') != track_id]
            
            # If no tracks were removed, return False
            if len(updated_tracks) == len(tracks):
                return False
                
            # Save updated playlist
            success, _ = await self.save_user_playlist(user_id, playlist_name, updated_tracks)
            return success
        except Exception as e:
            print(f"Error removing from playlist: {e}")
            return False
    
    async def delete_playlist(self, user_id: int, playlist_name: str) -> bool:
        """Delete a playlist"""
        try:
            playlist_file = os.path.join(self.playlists_dir, str(user_id), f"{playlist_name}.json")
            if not os.path.exists(playlist_file):
                return False
                
            os.remove(playlist_file)
            return True
        except Exception as e:
            print(f"Error deleting playlist: {e}")
            return False
    
    async def update_listen_history(self, user_id: int, track: Dict):
        """Update a user's listening history"""
        if str(user_id) not in self.user_history:
            self.user_history[str(user_id)] = []
            
        # Add track to history
        track_id = track.get('videoid')
        
        # Remove if already exists (to move it to the front)
        self.user_history[str(user_id)] = [t for t in self.user_history[str(user_id)] if t.get('videoid') != track_id]
        
        # Add to front of history
        self.user_history[str(user_id)].insert(0, track)
        
        # Keep only the last 50 tracks
        self.user_history[str(user_id)] = self.user_history[str(user_id)][:50]
        
        # Save history
        await self.save_user_playlist(user_id, "_history", self.user_history[str(user_id)])
    
    async def get_listen_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get a user's listening history"""
        # Try to load from memory
        if str(user_id) in self.user_history:
            return self.user_history[str(user_id)][:limit]
            
        # Otherwise load from file
        history = await self.get_playlist_tracks(user_id, "_history")
        
        # Update in-memory history
        self.user_history[str(user_id)] = history
        
        return history[:limit]
    
    async def get_personalized_recommendations(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Generate personalized recommendations based on a user's listening history"""
        try:
            # Get user's listening history
            history = await self.get_listen_history(user_id)
            
            if not history:
                return []
                
            # Extract artists and titles from history
            artists = []
            titles = []
            for track in history:
                if 'artist' in track and track['artist']:
                    artists.append(track['artist'])
                if 'title' in track and track['title']:
                    titles.append(track['title'])
            
            # Return empty list if no data available
            if not artists and not titles:
                return []
                
            # Look through all user playlists to find similar tracks
            all_tracks = []
            playlists_dir = self.playlists_dir
            
            # Check if playlists directory exists before trying to read from it
            if not os.path.exists(playlists_dir):
                self.ensure_playlist_dir()
                return []  # Return empty list if directory was just created
                
            for user_folder in os.listdir(playlists_dir):
                user_path = os.path.join(playlists_dir, user_folder)
                if os.path.isdir(user_path):
                    for playlist_file in os.listdir(user_path):
                        if playlist_file.endswith('.json') and playlist_file != '_history.json':
                            file_path = os.path.join(user_path, playlist_file)
                            try:
                                if os.path.exists(file_path):
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        try:
                                            playlist_tracks = json.load(f)
                                            all_tracks.extend(playlist_tracks)
                                        except json.JSONDecodeError:
                                            print(f"Warning: Invalid JSON in {file_path}")
                                        except Exception as e:
                                            print(f"Error reading playlist file {file_path}: {e}")
                            except Exception as e:
                                print(f"Error accessing file {file_path}: {e}")
            
            # Deduplicate tracks
            seen_ids = set()
            unique_tracks = []
            for track in all_tracks:
                track_id = track.get('videoid')
                if track_id and track_id not in seen_ids:
                    seen_ids.add(track_id)
                    unique_tracks.append(track)
            
            # Filter out tracks that are already in the user's history
            history_ids = set(track.get('videoid') for track in history)
            recommendations = [
                track for track in unique_tracks 
                if track.get('videoid') not in history_ids
            ]
            
            # If we don't have enough recommendations, just return what we have
            if len(recommendations) < limit:
                random.shuffle(recommendations)
                return recommendations
            
            # Otherwise, prioritize based on artist/title matches
            scored_tracks = []
            for track in recommendations:
                score = 0
                if 'artist' in track and track['artist']:
                    for artist in artists:
                        if artist.lower() in track['artist'].lower() or track['artist'].lower() in artist.lower():
                            score += 3
                            
                if 'title' in track and track['title']:
                    for title in titles:
                        if any(word in track['title'].lower() for word in title.lower().split()):
                            score += 1
                            
                scored_tracks.append((score, track))
            
            # Sort by score (descending) and return top tracks
            scored_tracks.sort(reverse=True, key=lambda x: x[0])
            return [track for _, track in scored_tracks[:limit]]
            
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return []

# Create a singleton instance
playlist_manager = PlaylistManager()

# Async function to get personalized playlist suggestions
async def get_personalized_playlist_suggestions(user_id: int, limit: int = 10) -> List[Dict]:
    """Get personalized playlist suggestions for a user"""
    return await playlist_manager.get_personalized_recommendations(user_id, limit)

# Function to add a song to user's history
async def add_to_user_history(user_id: int, track: Dict):
    """Add a song to a user's listening history"""
    await playlist_manager.update_listen_history(user_id, track)

# Function to export a playlist to a shareable format
async def export_playlist(user_id: int, playlist_name: str) -> str:
    """Export a playlist to a shareable format"""
    try:
        tracks = await playlist_manager.get_playlist_tracks(user_id, playlist_name)
        if not tracks:
            return None
            
        # Create a shareable string with track info
        shareable = f"📋 Playlist: {playlist_name}\n"
        shareable += f"🎵 {len(tracks)} tracks\n\n"
        
        for i, track in enumerate(tracks, 1):
            title = track.get('title', 'Unknown')
            duration = track.get('duration', 'Unknown')
            shareable += f"{i}. {title} ({duration})\n"
            
        return shareable
    except Exception as e:
        print(f"Error exporting playlist: {e}")
        return None
