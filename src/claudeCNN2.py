import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
import random
import sys
import os

# Add parent directory to path to import game module
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.game import Game

class LineGameEnvironment:
    """Wrapper for the Game class to work with DQN training."""
    
    def __init__(self, num_rows=7, num_cols=7, score_cutoff=0, handicap=5.5):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.score_cutoff = score_cutoff
        self.handicap = handicap
        self.game = None
        self.reset()
    
    def reset(self):
        """Reset the game to initial state."""
        self.game = Game(self.num_rows, self.num_cols, self.score_cutoff, self.handicap)
        board = self._convert_board_to_numpy(self.game.getBoard())
        current_player = self.game.getCurrentPlayer()
        return board, current_player
    
    def _convert_board_to_numpy(self, board):
        """Convert the game's board to numpy array."""
        return np.array(board, dtype=np.int32)
    
    def get_valid_actions(self):
        """Return list of valid (row, col) tuples for empty cells."""
        return self.game.getPossibleMoves()
    
    def step(self, action):
        """
        Execute action for current player.
        
        Args:
            action: Tuple (row, col) where current player places their tile
            
        Returns:
            next_state: Board after move
            reward: Reward for CURRENT player (relative to them)
            done: Whether game is over
            info: Dictionary with additional info
        """
        row, col = action
        current_player = self.game.getCurrentPlayer()
        
        # Get scores before move
        p1_before, p2_before = self.game.getPlayerScores()
        
        # Make the move
        result = self.game.playMove(row, col)
        
        if result == -1:
            # Invalid move - this shouldn't happen if we only select valid actions
            return self._convert_board_to_numpy(self.game.getBoard()), -1, True, {'invalid_move': True}
        
        # Get scores after move
        p1_after, p2_after = self.game.getPlayerScores()
        
        # Calculate move score for info
        if current_player == 1:
            move_score = p1_after - p1_before
        else:
            move_score = p2_after - p2_before
        
        # All moves have 0 reward by default
        reward = 0
        
        # Check if game is done
        winner = self.game.getWinner()
        done = (winner != 0)
        
        # Only assign reward at end of game: +1 for win, -1 for loss
        if done:
            if winner == current_player:
                reward = 1  # Win
            else:
                reward = -1  # Loss
        
        info = {
            'scores': self.game.getPlayerScores(),
            'move_score': move_score,
            'player': current_player,
            'winner': winner
        }
        
        # Get next state
        next_state = self._convert_board_to_numpy(self.game.getBoard())
        
        return next_state, reward, done, info


class BoardEncoder:
    """Encode board state from current player's perspective."""
    
    def __init__(self, num_rows=7, num_cols=7):
        self.board_size_rows = num_rows
        self.board_size_cols = num_cols
        self.num_channels = 3  # [empty, my_tiles, opponent_tiles]
    
    def encode(self, board, current_player):
        """
        Convert board to one-hot encoded features from current player's perspective.
        
        Args:
            board: numpy array of shape (rows, cols) with values {0, 1, 2}
            current_player: 1 or 2
            
        Returns:
            features: numpy array of shape (rows, cols, 3)
                Channel 0: Empty cells
                Channel 1: Current player's tiles
                Channel 2: Opponent's tiles
        """
        features = np.zeros((self.board_size_rows, self.board_size_cols, 3), dtype=np.float32)
        
        opponent = 3 - current_player
        
        features[:, :, 0] = (board == 0)  # Empty cells
        features[:, :, 1] = (board == current_player)  # My tiles
        features[:, :, 2] = (board == opponent)  # Opponent's tiles
        
        return features


class DQN(nn.Module):
    """Deep Q-Network for the line game."""
    
    def __init__(self, num_rows=7, num_cols=7, input_channels=3):
        super().__init__()
        
        self.num_rows = num_rows
        self.num_cols = num_cols
        
        # Convolutional layers to extract spatial features
        self.conv = nn.Sequential(
            nn.Conv2d(input_channels, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.ReLU(),
        )
        
        # Fully connected layers
        # After conv: rows*cols*128
        conv_output_size = num_rows * num_cols * 128
        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(conv_output_size, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, num_rows * num_cols)  # One action per cell
        )
    
    def forward(self, x):
        """
        Args:
            x: Board state tensor of shape (batch, rows, cols, 3)
        Returns:
            Q-values: Tensor of shape (batch, rows*cols)
        """
        # Convert from (batch, H, W, C) to (batch, C, H, W)
        if x.dim() == 4 and x.shape[-1] == 3:
            x = x.permute(0, 3, 1, 2)
        
        features = self.conv(x)
        q_values = self.fc(features)
        return q_values


class DQNAgent:
    """DQN agent that learns to play for either player."""
    
    def __init__(self, num_rows=7, num_cols=7, learning_rate=0.0001, gamma=0.95, epsilon=1.0, 
                 epsilon_decay=0.9995, epsilon_min=0.05):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.num_rows = num_rows
        self.num_cols = num_cols
        
        self.q_network = DQN(num_rows, num_cols).to(self.device)
        self.target_network = DQN(num_rows, num_cols).to(self.device)
        self.target_network.load_state_dict(self.q_network.state_dict())
        
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)
        self.loss_fn = nn.SmoothL1Loss()  # Huber loss - more stable than MSE
        
        self.encoder = BoardEncoder(num_rows, num_cols)
        self.memory = deque(maxlen=50000)  # Larger replay buffer
        
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        
        self.batch_size = 128  # Larger batch size
    
    def action_to_index(self, action):
        """Convert (row, col) to flat action index."""
        row, col = action
        return row * self.num_cols + col
    
    def index_to_action(self, index):
        """Convert flat action index to (row, col)."""
        row = index // self.num_cols
        col = index % self.num_cols
        return (row, col)
    
    def select_action(self, state, current_player, valid_actions, epsilon=None):
        """Select action using epsilon-greedy policy."""
        if epsilon is None:
            epsilon = self.epsilon
            
        if random.random() < epsilon:
            # Random action
            return random.choice(valid_actions)
        else:
            # Greedy action based on Q-values
            state_tensor = torch.FloatTensor(
                self.encoder.encode(state, current_player)
            ).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                q_values = self.q_network(state_tensor).squeeze()
            
            # Mask invalid actions with very negative values
            valid_indices = [self.action_to_index(a) for a in valid_actions]
            masked_q_values = torch.full_like(q_values, float('-inf'))
            masked_q_values[valid_indices] = q_values[valid_indices]
            
            best_idx = torch.argmax(masked_q_values).item()
            return self.index_to_action(best_idx)
    
    def store_transition(self, state, player, action, reward, next_state, next_player, done):
        """Store transition in replay memory."""
        self.memory.append((state, player, action, reward, next_state, next_player, done))
    
    def train_step(self):
        """Perform one training step using experience replay."""
        if len(self.memory) < self.batch_size:
            return None
        
        # Sample batch
        batch = random.sample(self.memory, self.batch_size)
        
        # Pre-allocate numpy arrays for efficiency
        states_np = np.zeros((self.batch_size, self.num_rows, self.num_cols, 3), dtype=np.float32)
        next_states_np = np.zeros((self.batch_size, self.num_rows, self.num_cols, 3), dtype=np.float32)
        actions_np = np.zeros(self.batch_size, dtype=np.int64)
        rewards_np = np.zeros(self.batch_size, dtype=np.float32)
        dones_np = np.zeros(self.batch_size, dtype=np.float32)
        
        # Fill arrays
        for i, (s, p, a, r, ns, np_player, d) in enumerate(batch):
            states_np[i] = self.encoder.encode(s, p)
            next_states_np[i] = self.encoder.encode(ns, np_player)
            actions_np[i] = self.action_to_index(a)
            rewards_np[i] = r
            dones_np[i] = d
        
        # Convert to tensors (much faster from single numpy array)
        states = torch.from_numpy(states_np).to(self.device)
        next_states = torch.from_numpy(next_states_np).to(self.device)
        actions = torch.from_numpy(actions_np).to(self.device)
        rewards = torch.from_numpy(rewards_np).to(self.device)
        dones = torch.from_numpy(dones_np).to(self.device)
        
        # Current Q-values
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1)).squeeze()
        
        # Target Q-values
        with torch.no_grad():
            # Get maximum Q-value for next state
            next_q_values = self.target_network(next_states).max(1)[0]
            # For two-player zero-sum: opponent's best move is our worst outcome
            # But we still want to maximize our long-term return
            target_q_values = rewards + (1 - dones) * self.gamma * next_q_values
        
        # Compute loss and update
        loss = self.loss_fn(current_q_values, target_q_values)
        
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), 1.0)
        self.optimizer.step()
        
        return loss.item()
    
    def update_target_network(self):
        """Copy weights from Q-network to target network."""
        self.target_network.load_state_dict(self.q_network.state_dict())
    
    def decay_epsilon(self):
        """Decay exploration rate."""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
    
    def save_checkpoint(self, filepath='dqn_checkpoint.pth'):
        """
        Save model weights and training state.
        
        Args:
            filepath: Path to save the checkpoint
        """
        checkpoint = {
            'q_network_state_dict': self.q_network.state_dict(),
            'target_network_state_dict': self.target_network.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'gamma': self.gamma,
            'epsilon_decay': self.epsilon_decay,
            'epsilon_min': self.epsilon_min
        }
        torch.save(checkpoint, filepath)
        print(f"Checkpoint saved to {filepath}")
    
    def load_checkpoint(self, filepath='dqn_checkpoint.pth'):
        """
        Load model weights and training state.
        
        Args:
            filepath: Path to load the checkpoint from
        """
        checkpoint = torch.load(filepath, map_location=self.device)
        
        self.q_network.load_state_dict(checkpoint['q_network_state_dict'])
        self.target_network.load_state_dict(checkpoint['target_network_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.epsilon = checkpoint['epsilon']
        self.gamma = checkpoint['gamma']
        self.epsilon_decay = checkpoint['epsilon_decay']
        self.epsilon_min = checkpoint['epsilon_min']
        
        print(f"Checkpoint loaded from {filepath}")
        print(f"Resumed with epsilon={self.epsilon:.3f}")


def play_self_play_episode(env, agent, train=True):
    """Play one episode of self-play."""
    state, current_player = env.reset()
    episode_data = []
    done = False
    
    while not done:
        valid_actions = env.get_valid_actions()
        if not valid_actions:
            break
        
        # Agent selects action
        action = agent.select_action(state, current_player, valid_actions)
        next_state, reward, done, info = env.step(action)
        
        # Store transition
        next_player = env.game.getCurrentPlayer()
        episode_data.append((state.copy(), current_player, action, reward, 
                           next_state.copy(), next_player, done))
        
        state = next_state
        current_player = next_player
    
    # Add transitions to memory
    if train:
        for i, (s, p, a, r, ns, np, d) in enumerate(episode_data):
            agent.store_transition(s, p, a, r, ns, np, d)
    
    scores = env.game.getPlayerScores()
    return {1: scores[0], 2: scores[1]}, episode_data


def train_agent(num_episodes=10000, num_rows=7, num_cols=7, score_cutoff=0, handicap=5.5,
                verbose=True, save_every=1000, checkpoint_path='dqn_checkpoint.pth'):
    """Train the DQN agent via self-play."""
    env = LineGameEnvironment(num_rows, num_cols, score_cutoff, handicap)
    agent = DQNAgent(num_rows, num_cols)
    agent.load_checkpoint('dqn_checkpoint_final.pth')
    
    episode_results = []
    losses = []
    
    for episode in range(num_episodes):
        scores, _ = play_self_play_episode(env, agent, train=True)
        
        # Train on accumulated experience - start immediately
        episode_losses = []
        if len(agent.memory) >= agent.batch_size:
            # More frequent training
            for _ in range(5):
                loss = agent.train_step()
                if loss is not None:
                    episode_losses.append(loss)
        
        episode_results.append(scores)
        if episode_losses:
            losses.append(np.mean(episode_losses))
        
        agent.decay_epsilon()
        
        # Update target network more frequently
        if episode % 5 == 0 and episode > 0:
            agent.update_target_network()
        
        # Save checkpoint periodically
        if episode > 0 and episode % save_every == 0:
            agent.save_checkpoint(checkpoint_path)
        
        if verbose and episode % 100 == 0:
            recent = episode_results[-100:] if episode >= 100 else episode_results
            avg_p1 = np.mean([s[1] for s in recent])
            avg_p2 = np.mean([s[2] for s in recent])
            recent_loss = np.mean(losses[-100:]) if losses else 0
            print(f"Episode {episode}")
            print(f"  Avg Player 1 Score: {avg_p1:.1f}, Avg Player 2 Score: {avg_p2:.1f}")
            print(f"  Epsilon: {agent.epsilon:.3f}, Avg Loss: {recent_loss:.4f}")
            print(f"  Memory size: {len(agent.memory)}")
    
    # Save final checkpoint
    agent.save_checkpoint(checkpoint_path.replace('.pth', '_final.pth'))
    
    return agent, episode_results


if __name__ == "__main__":
    print("Training DQN agent on turn-based line game...")
    print("Using the Game class from src/game.py")
    print("Player 1 places 1s, Player 2 places 2s")
    print("Scoring: Lines of length n score 2^(n-1) points")
    print()
    
    # Configure game parameters
    NUM_ROWS = 7
    NUM_COLS = 7
    SCORE_CUTOFF = 0  # 0 means play until board is full
    HANDICAP = 5.5
    
    print(f"Board size: {NUM_ROWS}x{NUM_COLS}")
    print(f"Score cutoff: {SCORE_CUTOFF if SCORE_CUTOFF > 0 else 'None (play to fill board)'}")
    print(f"Handicap: {HANDICAP}")
    print()
    
    # Train the agent
    agent, results = train_agent(
        num_episodes=50000, 
        num_rows=NUM_ROWS,
        num_cols=NUM_COLS,
        score_cutoff=SCORE_CUTOFF,
        handicap=HANDICAP,
        verbose=True, 
        save_every=100
    )
    
    print("\nTraining complete!")
    print(f"Final epsilon: {agent.epsilon:.3f}")
    
    # Analyze final performance
    final_results = results[-100:]
    p1_scores = [s[1] for s in final_results]
    p2_scores = [s[2] for s in final_results]
    
    print(f"\nLast 100 episodes:")
    print(f"  Player 1 avg: {np.mean(p1_scores):.1f}")
    print(f"  Player 2 avg: {np.mean(p2_scores):.1f}")
    print(f"  Player 1 wins: {sum(1 for s in final_results if s[1] > s[2])}")
    print(f"  Player 2 wins: {sum(1 for s in final_results if s[2] > s[1])}")
    print(f"  Ties: {sum(1 for s in final_results if s[1] == s[2])}")
    
    print("\n" + "="*50)
    print("To load the trained model later:")
    print(f"  agent = DQNAgent(num_rows={NUM_ROWS}, num_cols={NUM_COLS})")
    print("  agent.load_checkpoint('dqn_checkpoint_final.pth')")
    print("="*50)