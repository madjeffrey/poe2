import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
import random

from game import Game

class LineGameEnvironment:
    """
    Two-player 7x7 board game where:
    - Player 1 places 1s
    - Player 2 places 2s
    - Lines of length n score 2^(n-1) points
    """
    
    def __init__(self):
        self.board_size = 7
        self.reset()
    
    def reset(self):
        """Reset the board to empty state."""
        self.board = np.zeros((self.board_size, self.board_size), dtype=np.int32)
        self.current_player = 1  # Player 1 starts
        self.scores = {1: 0, 2: 0}  # Track cumulative scores
        return self.board.copy(), self.current_player
    
    def get_valid_actions(self):
        """Return list of valid (row, col) tuples for empty cells."""
        actions = []
        for i in range(self.board_size):
            for j in range(self.board_size):
                if self.board[i, j] == 0:
                    actions.append((i, j))
        return actions
    
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
        
        if self.board[row, col] != 0:
            # Invalid move - penalize current player
            return self.board.copy(), -100, True, {'invalid_move': True}
        
        # Place the tile for current player
        value = self.current_player
        self.board[row, col] = value
        
        # Calculate score for this move
        move_score = self._calculate_line_score(row, col, value)
        self.scores[self.current_player] += move_score
        
        # Reward is relative to current player
        reward = move_score
        
        # Check if game is done (board full)
        done = not np.any(self.board == 0)
        
        # Add final game outcome to reward if done
        if done:
            score_diff = self.scores[self.current_player] - self.scores[3 - self.current_player]
            if score_diff > 0:
                reward += 100  # Win bonus
            elif score_diff < 0:
                reward -= 100  # Loss penalty
            # Tie gives no additional reward
        
        info = {
            'scores': self.scores.copy(),
            'move_score': move_score,
            'player': self.current_player
        }
        
        # Switch players
        self.current_player = 3 - self.current_player
        
        return self.board.copy(), reward, done, info
    
    def _calculate_line_score(self, row, col, value):
        """Calculate score for lines passing through the placed tile."""
        total_score = 0
        
        # Check horizontal line
        total_score += self._score_line_at(row, col, value, 0, 1)
        
        # Check vertical line
        total_score += self._score_line_at(row, col, value, 1, 0)
        
        # Check diagonal (top-left to bottom-right)
        total_score += self._score_line_at(row, col, value, 1, 1)
        
        # Check anti-diagonal (top-right to bottom-left)
        total_score += self._score_line_at(row, col, value, 1, -1)
        
        return total_score
    
    def _score_line_at(self, row, col, value, dr, dc):
        """
        Score a line in direction (dr, dc) passing through (row, col).
        Returns 2^(n-1) where n is the length of consecutive matching tiles.
        """
        # Count consecutive tiles in negative direction
        count_neg = 0
        r, c = row - dr, col - dc
        while 0 <= r < self.board_size and 0 <= c < self.board_size:
            if self.board[r, c] == value:
                count_neg += 1
                r -= dr
                c -= dc
            else:
                break
        
        # Count consecutive tiles in positive direction
        count_pos = 0
        r, c = row + dr, col + dc
        while 0 <= r < self.board_size and 0 <= c < self.board_size:
            if self.board[r, c] == value:
                count_pos += 1
                r += dr
                c += dc
            else:
                break
        
        # Total line length includes the placed tile
        line_length = count_neg + 1 + count_pos
        
        # Score is 2^(n-1) for line of length n
        if line_length >= 2:
            return 2 ** (line_length - 1)
        return 0


class BoardEncoder:
    """Encode board state from current player's perspective."""
    
    def __init__(self):
        self.board_size = 7
        self.num_channels = 3  # [empty, my_tiles, opponent_tiles]
    
    def encode(self, board, current_player):
        """
        Convert board to one-hot encoded features from current player's perspective.
        
        Args:
            board: numpy array of shape (7, 7) with values {0, 1, 2}
            current_player: 1 or 2
            
        Returns:
            features: numpy array of shape (7, 7, 3)
                Channel 0: Empty cells
                Channel 1: Current player's tiles
                Channel 2: Opponent's tiles
        """
        features = np.zeros((self.board_size, self.board_size, 3), dtype=np.float32)
        
        opponent = 3 - current_player
        
        features[:, :, 0] = (board == 0)  # Empty cells
        features[:, :, 1] = (board == current_player)  # My tiles
        features[:, :, 2] = (board == opponent)  # Opponent's tiles
        
        return features


class DQN(nn.Module):
    """Deep Q-Network for 7x7 line game."""
    
    def __init__(self, input_channels=3):
        super().__init__()
        
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
        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(7 * 7 * 128, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 7 * 7)  # 49 actions (one per cell)
        )
    
    def forward(self, x):
        """
        Args:
            x: Board state tensor of shape (batch, 7, 7, 3)
        Returns:
            Q-values: Tensor of shape (batch, 49)
        """
        # Convert from (batch, H, W, C) to (batch, C, H, W)
        if x.dim() == 4 and x.shape[-1] == 3:
            x = x.permute(0, 3, 1, 2)
        
        features = self.conv(x)
        q_values = self.fc(features)
        return q_values


class DQNAgent:
    """DQN agent that learns to play for either player."""
    
    def __init__(self, learning_rate=0.001, gamma=0.99, epsilon=1.0, epsilon_decay=0.995, epsilon_min=0.01):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.q_network = DQN().to(self.device)
        self.target_network = DQN().to(self.device)
        self.target_network.load_state_dict(self.q_network.state_dict())
        
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=learning_rate)
        self.loss_fn = nn.MSELoss()
        
        self.encoder = BoardEncoder()
        self.memory = deque(maxlen=10000)
        
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        
        self.batch_size = 64
    
    def action_to_index(self, action):
        """Convert (row, col) to flat action index."""
        row, col = action
        return row * 7 + col
    
    def index_to_action(self, index):
        """Convert flat action index to (row, col)."""
        row = index // 7
        col = index % 7
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
        
        states = torch.FloatTensor([
            self.encoder.encode(s, p) for s, p, _, _, _, _, _ in batch
        ]).to(self.device)
        
        actions = torch.LongTensor([
            self.action_to_index(a) for _, _, a, _, _, _, _ in batch
        ]).to(self.device)
        
        rewards = torch.FloatTensor([r for _, _, _, r, _, _, _ in batch]).to(self.device)
        
        next_states = torch.FloatTensor([
            self.encoder.encode(ns, np) for _, _, _, _, ns, np, _ in batch
        ]).to(self.device)
        
        dones = torch.FloatTensor([d for _, _, _, _, _, _, d in batch]).to(self.device)
        
        # Current Q-values
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1)).squeeze()
        
        # Target Q-values (from opponent's perspective after their move)
        with torch.no_grad():
            next_q_values = self.target_network(next_states).max(1)[0]
            # Note: next state is from opponent's perspective, so we negate their future value
            target_q_values = rewards + (1 - dones) * self.gamma * (-next_q_values)
        
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


def play_self_play_episode(env, agent, train=True):
    """Play one episode of self-play."""
    # do I need to reset/ remake game object
    state, current_player = env.getBoard(), env.getCurrentPlayer()
    episode_data = []
    done = False
    
    while not done:
        valid_actions = env.getPossibleMoves()
        if not valid_actions:
            break
        
        # Agent selects action
        action = agent.select_action(state, current_player, valid_actions)
        env.playMove(action[0], action[1])
        next_state = env.getBoard().copy()
        reward = 1 if env.getCurrentPlayer() == env.getWinner() else -1
        done = env.gameOver()
        
        # Store transition
        next_player = env.getCurrentPlayer()
        episode_data.append((state.copy(), current_player, action, reward, next_state.copy(), next_player, done))
        
        state = next_state
        current_player = next_player
    
    # Add transitions to memory with proper rewards
    # The last player got their final reward, previous moves need adjustment
    if train:
        for i, (s, p, a, r, ns, np, d) in enumerate(episode_data):
            agent.store_transition(s, p, a, r, ns, np, d)
    
    return env.getPlayerScores(), episode_data


def train_agent(num_episodes=1000, verbose=True):
    """Train the DQN agent via self-play."""
    env = Game(7,7,0,5.5)
    agent = DQNAgent()
    
    episode_results = []
    
    for episode in range(num_episodes):
        scores, _ = play_self_play_episode(env, agent, train=True)
        
        episode_losses = []
        if len(agent.memory) >= agent.batch_size:
            # More frequent training
            for _ in range(5):
                loss = agent.train_step()
                if loss is not None:
                    episode_losses.append(loss)
        
        episode_results.append(scores)
        agent.decay_epsilon()
        
        # Update target network periodically
        if episode % 10 == 0:
            agent.update_target_network()
        
        if verbose and episode % 50 == 0:
            recent = episode_results[-50:] if episode >= 50 else episode_results
            avg_p1 = np.mean([s[0] for s in recent])
            avg_p2 = np.mean([s[1] for s in recent])
            print(f"Episode {episode}")
            print(f"  Avg Player 1 Score: {avg_p1:.1f}, Avg Player 2 Score: {avg_p2:.1f}")
            print(f"  Epsilon: {agent.epsilon:.3f}")
    
    return agent, episode_results


if __name__ == "__main__":
    print("Training DQN agent on 7x7 turn-based line game...")
    print("Player 1 places 1s, Player 2 places 2s")
    print("Scoring: Lines of length n score 2^(n-1) points")
    print()
    
    # Train the agent
    agent, results = train_agent(num_episodes=50000, verbose=True)
    
    print("\nTraining complete!")
    print(f"Final epsilon: {agent.epsilon:.3f}")
    
    # Analyze final performance
    final_results = results[-100:]
    p1_scores = [s[0] for s in final_results]
    p2_scores = [s[1] for s in final_results]
    
    print(f"\nLast 100 episodes:")
    print(f"  Player 1 avg: {np.mean(p1_scores):.1f}")
    print(f"  Player 2 avg: {np.mean(p2_scores):.1f}")
    print(f"  Player 1 wins: {sum(1 for s in final_results if s[0] > s[1])}")
    print(f"  Player 2 wins: {sum(1 for s in final_results if s[1] > s[0])}")
    print(f"  Ties: {sum(1 for s in final_results if s[0] == s[1])}")