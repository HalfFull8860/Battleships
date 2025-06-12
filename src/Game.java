import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
// The front-end team must add the org.json library to their project dependencies
import org.json.JSONArray;
import org.json.JSONObject;

public class Game extends JFrame {

    private static final int BOARD_SIZE = 10;

    // UI Components
    private final JButton[][] board1Buttons = new JButton[BOARD_SIZE][BOARD_SIZE];
    private final JButton[][] board2Buttons = new JButton[BOARD_SIZE][BOARD_SIZE];
    private JLabel statusLabel;
    private JLabel player1Label;
    private JLabel player2Label;
    private javax.swing.Timer pollingTimer;

    // State variables driven by the backend
    private String gameId;
    private int playerId;
    private boolean isMyTurn;
    private String player1Name = "Player 1";
    private String player2Name = "Player 2";
    private boolean isTwoPlayerMode = false;

    public Game() {
        createUserInterface();
        // The game setup is now the very first thing the user does.
        startGameSetup();
    }

    private void createUserInterface() {
        setTitle("Battleship Game");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(1200, 600);
        setLocationRelativeTo(null);

        JPanel mainPanel = new JPanel(new BorderLayout());
        mainPanel.add(createTopPanel(), BorderLayout.NORTH);
        mainPanel.add(createGameBoards(), BorderLayout.CENTER);
        add(mainPanel);
    }

    private JPanel createTopPanel() {
        JPanel topPanel = new JPanel(new BorderLayout());
        statusLabel = new JLabel("Welcome to Battleship! Please Create or Join a Game.", SwingConstants.CENTER);
        statusLabel.setFont(new Font("Arial", Font.BOLD, 18));
        topPanel.add(statusLabel, BorderLayout.CENTER);

        JPanel controlPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT));
        JButton newGameButton = new JButton("New Game");
        newGameButton.addActionListener(e -> restartGame());
        controlPanel.add(newGameButton);
        topPanel.add(controlPanel, BorderLayout.EAST);

        return topPanel;
    }

    private JPanel createGameBoards() {
        JPanel boardsPanel = new JPanel(new GridLayout(1, 2, 20, 0));
        boardsPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        JPanel board1Panel = createSingleBoard(board1Buttons, "Your Board", true);
        this.player1Label = (JLabel) board1Panel.getComponent(0);
        boardsPanel.add(board1Panel);

        JPanel board2Panel = createSingleBoard(board2Buttons, "Opponent's Board", false);
        this.player2Label = (JLabel) board2Panel.getComponent(0);
        boardsPanel.add(board2Panel);

        return boardsPanel;
    }

    private JPanel createSingleBoard(JButton[][] buttons, String title, boolean isPlayer1Board) {
        JPanel boardPanel = new JPanel(new BorderLayout(0, 5));
        JLabel titleLabel = new JLabel(title, SwingConstants.CENTER);
        titleLabel.setFont(new Font("Arial", Font.BOLD, 16));
        boardPanel.add(titleLabel, BorderLayout.NORTH);

        JPanel gridPanel = new JPanel(new GridLayout(BOARD_SIZE, BOARD_SIZE));
        gridPanel.setBorder(BorderFactory.createLineBorder(Color.BLACK));
        for (int row = 0; row < BOARD_SIZE; row++) {
            for (int col = 0; col < BOARD_SIZE; col++) {
                buttons[row][col] = new JButton();
                buttons[row][col].setPreferredSize(new Dimension(45, 45));
                buttons[row][col].setBackground(Color.LIGHT_GRAY);
                buttons[row][col].setFont(new Font("Arial", Font.BOLD, 16));

                final int r = row;
                final int c = col;
                buttons[row][col].addActionListener(e -> handleBoardClick(r, c, isPlayer1Board));
                gridPanel.add(buttons[row][col]);
            }
        }
        boardPanel.add(gridPanel, BorderLayout.CENTER);
        return boardPanel;
    }
    
    // NEW: This is the main setup method with Create/Join logic
    private void startGameSetup() {
        String[] setupOptions = {"Create Game", "Join Game"};
        int setupChoice = JOptionPane.showOptionDialog(this, "Welcome to Battleship!", "Setup",
            JOptionPane.DEFAULT_OPTION, JOptionPane.INFORMATION_MESSAGE, null, setupOptions, setupOptions[0]);

        if (setupChoice == -1) System.exit(0);

        if (setupChoice == 0) { // CREATE GAME
            createGameFlow();
        } else { // JOIN GAME
            joinGameFlow();
        }
    }

    private void createGameFlow() {
        String[] modeOptions = {"Player vs. Bot", "Player vs. Player"};
        int modeChoice = JOptionPane.showOptionDialog(this, "Choose your game mode:", "Create Game",
            JOptionPane.DEFAULT_OPTION, JOptionPane.INFORMATION_MESSAGE, null, modeOptions, modeOptions[0]);

        if (modeChoice == -1) System.exit(0);

        this.isTwoPlayerMode = (modeChoice == 1);
        String mode = this.isTwoPlayerMode ? "vs_player" : "vs_bot";
        
        Integer[] gameCounts = {1, 3, 5};
        Integer numGames = (Integer) JOptionPane.showInputDialog(this, "Best of:", "Match Setup",
            JOptionPane.QUESTION_MESSAGE, null, gameCounts, gameCounts[0]);

        if (numGames == null) System.exit(0);

        getPlayerNames(this.isTwoPlayerMode);

        String[] createResponse = BattleshipConnector.createGame(mode, this.player1Name, this.player2Name, numGames);
        
        this.gameId = createResponse[0];
        this.playerId = 0; // Creator is always Player 1

        if (this.gameId.isEmpty()) {
            JOptionPane.showMessageDialog(this, "Error creating game: " + createResponse[1], "API Error", JOptionPane.ERROR_MESSAGE);
            System.exit(1);
        }

        if(this.isTwoPlayerMode) {
            JTextArea textArea = new JTextArea("Game created! Share this ID with Player 2:\n" + this.gameId);
            textArea.setEditable(false);
            JOptionPane.showMessageDialog(this, textArea, "Game ID", JOptionPane.INFORMATION_MESSAGE);
        }
        
        refreshGameState();
    }

    private void joinGameFlow() {
        this.isTwoPlayerMode = true; // Joining implies a two-player game
        this.gameId = JOptionPane.showInputDialog(this, "Enter the Game ID from Player 1:", "Join Game", JOptionPane.QUESTION_MESSAGE);

        if (this.gameId == null || this.gameId.trim().isEmpty()) {
            System.exit(0);
        }
        
        this.playerId = 1; // Joining player is always Player 2
        this.player1Name = "Player 1"; // Will be updated from server
        this.player2Name = "Player 2"; // Will be updated from server

        refreshGameState();
    }

    private void getPlayerNames(boolean isTwoPlayer) {
        this.player1Name = JOptionPane.showInputDialog(this, "Enter Player 1's Name:", "Player Setup", JOptionPane.QUESTION_MESSAGE);
        if (this.player1Name == null || this.player1Name.trim().isEmpty()) this.player1Name = "Player 1";

        if (isTwoPlayer) {
            this.player2Name = JOptionPane.showInputDialog(this, "Enter Player 2's Name:", "Player Setup", JOptionPane.QUESTION_MESSAGE);
            if (this.player2Name == null || this.player2Name.trim().isEmpty()) this.player2Name = "Player 2";
        } else {
            this.player2Name = "Bot";
        }
    }

    private void refreshGameState() {
        String jsonResponse = BattleshipConnector.getGameState(this.gameId, this.playerId);
        updateUiFromJson(jsonResponse);
    }

    private void handleBoardClick(int row, int col, boolean isPlayer1Board) {
        if (isPlayer1Board || !this.isMyTurn) return;
        String jsonResponse = BattleshipConnector.attack(this.gameId, this.playerId, row, col);
        updateUiFromJson(jsonResponse);
    }
    
    private void startPolling() {
        if (pollingTimer != null && pollingTimer.isRunning()) return;
        pollingTimer = new javax.swing.Timer(3000, e -> refreshGameState());
        pollingTimer.setRepeats(true);
        pollingTimer.start();
    }

    private void updateUiFromJson(String jsonResponseString) {
        try {
            JSONObject responseJson = new JSONObject(jsonResponseString);

            if (responseJson.has("error")) {
                JOptionPane.showMessageDialog(this, responseJson.getString("error"), "Error", JOptionPane.ERROR_MESSAGE);
                if (pollingTimer != null) pollingTimer.stop();
                return;
            }

            JSONObject gameState = responseJson.getJSONObject("game_state");

            this.isMyTurn = (gameState.getInt("current_turn") == this.playerId) && !gameState.getBoolean("game_over");

            // Update local names from the authoritative source (the backend)
            this.player1Name = gameState.getString("player1_name");
            this.player2Name = gameState.getString("player2_name");
            
            // Update score and labels
            JSONObject wins = gameState.getJSONObject("wins");
            this.player1Label.setText(this.player1Name + " | Score: " + wins.get("0") + " | Sunk: " + gameState.getString("opponent_sinks"));
            this.player2Label.setText(this.player2Name + " | Score: " + wins.get("1") + " | Sunk: " + gameState.getString("your_sinks"));
            this.statusLabel.setText(gameState.getString("status_message"));

            updateBoard(board1Buttons, gameState.getJSONArray("your_board"));
            updateBoard(board2Buttons, gameState.getJSONArray("opponent_board"));

            if (!gameState.isNull("match_winner")) {
                this.isMyTurn = false;
                if(pollingTimer != null) pollingTimer.stop();
                String winnerName = gameState.getInt("match_winner") == 0 ? this.player1Name : this.player2Name;
                JOptionPane.showMessageDialog(this, "Match Over! Winner is " + winnerName, "Match Over", JOptionPane.INFORMATION_MESSAGE);
            } else if (isTwoPlayerMode) {
                if (this.isMyTurn || gameState.getBoolean("game_over")) {
                    if (pollingTimer != null) pollingTimer.stop();
                } else {
                    startPolling();
                }
            }
        } catch (Exception e) {
            System.err.println("Error parsing JSON response: " + jsonResponseString);
            e.printStackTrace();
        }
    }

    private void updateBoard(JButton[][] buttons, JSONArray boardData) {
        for (int r = 0; r < BOARD_SIZE; r++) {
            JSONArray boardRow = boardData.getJSONArray(r);
            for (int c = 0; c < BOARD_SIZE; c++) {
                String cell = boardRow.getString(c);
                switch (cell) {
                    case "S": // Your own, untouched ship
                        buttons[r][c].setBackground(Color.decode("#000000"));
                        buttons[r][c].setText(""); // FIX: Cleared button text
                        break;
                    case "~": // A confirmed miss on the opponent's board
                        buttons[r][c].setBackground(Color.decode("#6dfff6"));
                        buttons[r][c].setText("\u2022");
                        break;
                    case "O": // A miss on your own board
                        buttons[r][c].setBackground(Color.decode("#0078ff"));
                        buttons[r][c].setText("\u2022");
                        break;
                    case "x": // A hit ship part
                        buttons[r][c].setBackground(Color.decode("#ff8700"));
                        buttons[r][c].setText("X");
                        break;
                    case "X": // A fully sunk ship part
                        buttons[r][c].setBackground(Color.decode("#ff0000"));
                        buttons[r][c].setText("X");
                        break;
                    case "?":
                    default: // FIX: Corrected switch structure and color format
                        buttons[r][c].setBackground(Color.decode("#d3d3d3")); // Added '#'
                        buttons[r][c].setText(""); // FIX: Cleared button text
                        break;
                }
            }
        }
    }
    
    private void restartGame() {
        if(pollingTimer != null) pollingTimer.stop();
        this.dispose();
        SwingUtilities.invokeLater(() -> new Game().setVisible(true));
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new Game().setVisible(true));
    }
}