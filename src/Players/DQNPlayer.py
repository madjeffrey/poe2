from player import Player
from ..claudeCNN2 import DQN
import torch
import os



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
            board: list of lists (rows, cols) with values {0, 1, 2}
            current_player: 1 or 2
            
        Returns:
            features: numpy array of shape (rows, cols, 3)
        """
        # Convert to numpy if needed
        board_array = np.array(board, dtype=np.int32)
        
        features = np.zeros((self.board_size_rows, self.board_size_cols, 3), dtype=np.float32)
        
        opponent = 3 - current_player
        
        features[:, :, 0] = (board_array == 0)  # Empty cells
        features[:, :, 1] = (board_array == current_player)  # My tiles
        features[:, :, 2] = (board_array == opponent)  # Opponent's tiles
        
        return features
    
class DQNPlayer(Player):
    """
    Player that uses a trained DQN to select moves.
    Selects actions based on argmax Q(s,a).
    """
    
    
    def __init__(self, checkpoint_path='dqn_checkpoint_final.pth', name="dqnBot", num_rows=7, num_cols=7):
        """
        Args:
            checkpoint_path: Path to the saved DQN checkpoint
            name: Name of the player
            num_rows: Number of rows in the game board
            num_cols: Number of columns in the game board
        """
        self._desc = f"This player uses a trained Deep Q-Network to select optimal moves based on Q(s,a) values. Model: {checkpoint_path}"
        super().__init__(name)
        
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.checkpoint_path = checkpoint_path
        
        # Set device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Initialize encoder
        self.encoder = BoardEncoder(num_rows, num_cols)
        
        # Load the trained model
        self.model = DQN(num_rows, num_cols).to(self.device)
        self._load_model()
        
        # Set model to evaluation mode
        self.model.eval()
        
        print(f"DQN Player initialized with model from: {checkpoint_path}")
        print(f"Using device: {self.device}")
    
    def _load_model(self):
        """Load the trained model from checkpoint."""
        if not os.path.exists(self.checkpoint_path):
            raise FileNotFoundError(f"Checkpoint not found at: {self.checkpoint_path}")
        
        checkpoint = torch.load(self.checkpoint_path, map_location=self.device)
        
        # Load the Q-network weights
        self.model.load_state_dict(checkpoint['q_network_state_dict'])
        
        print(f"Model loaded successfully!")
        if 'epsilon' in checkpoint:
            print(f"Model was trained with final epsilon: {checkpoint['epsilon']:.3f}")
    
    def isTestable(self):
        """This player is testable."""
        return True
    
    def action_to_index(self, action):
        """Convert (row, col) to flat action index."""
        row, col = action
        return row * self.num_cols + col
    
    def index_to_action(self, index):
        """Convert flat action index to (row, col)."""
        row = index // self.num_cols
        col = index % self.num_cols
        return (row, col)
    
    def actionMove(self) -> tuple:
        """
        Select and play the best move according to Q-values.
        
        Returns:
            tuple: (row, col) of the move played
        """
        assert self._game, "no game: set the game"
        assert self._game.getCurrentPlayer() == self._playerOrder, \
            f"ERROR: not player {self._playerOrder}'s turn, but tries to play"
        
        # Get current board state
        board = self._game.getBoard()
        current_player = self._game.getCurrentPlayer()
        
        # Encode the board state
        state = self.encoder.encode(board, current_player)
        
        # Convert to tensor and add batch dimension
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        # Get Q-values from the network
        with torch.no_grad():
            q_values = self.model(state_tensor).squeeze()
        
        # Get valid actions (empty cells)
        valid_actions = self._game.getPossibleMoves()
        
        if not valid_actions:
            raise ValueError("No valid actions available!")
        
        # Mask invalid actions with very negative values
        valid_indices = [self.action_to_index(a) for a in valid_actions]
        masked_q_values = torch.full_like(q_values, float('-inf'))
        masked_q_values[valid_indices] = q_values[valid_indices]
        
        # Select action with highest Q-value (argmax)
        best_action_index = torch.argmax(masked_q_values).item()
        best_action = self.index_to_action(best_action_index)
        
        # Extract row and col
        self._row, self._col = best_action
        
        # Play the move
        result = self._game.playMove(self._row, self._col)
        
        if result == -1:
            raise ValueError(f"Illegal move attempted: {best_action}")
        
        return (self._row, self._col)