import javax.swing.*;
import java.awt.*;
import java.net.URL;
import org.json.JSONArray;
import org.json.JSONObject;

/**
 * The main class for the Battleship game client.
 * This class creates the user interface and handles all interaction with the backend API.
 * It functions as a "dumb client," meaning all game logic and state are managed by the server.
 */
public class Game extends JFrame {

    // A constant defining the size of the game grid.
    private static final int BOARD_SIZE = 10;

    // --- UI Components ---
    // These are final because they are initialized once and their references do not change.
    private final JButton[][] board1Buttons = new JButton[BOARD_SIZE][BOARD_SIZE];
    private final JButton[][] board2Buttons = new JButton[BOARD_SIZE][BOARD_SIZE];
    private JLabel statusLabel;
    private JLabel player1Label;
    private JLabel player2Label;
    private javax.swing.Timer pollingTimer; // Used in PvP mode to check for the opponent's move.

    // --- Client-Side State Variables ---
    // These variables store the current state of the game session as received from the backend.
    private String gameId;
    private int playerId;
    private boolean isMyTurn;
    private String player1Name = "Player 1";
    private String player2Name = "Player 2";
    private boolean isTwoPlayerMode = false;

    /**
     * The main constructor for the Game class.
     * It orchestrates the setup of the application by loading resources, creating the UI,
     * and then running the game setup flow.
     */
    public Game() {
        createUserInterface();
        startGameSetup();
    }

    /**
     * Initializes the main JFrame window, sets its properties, and lays out the main panels.
     */
    private void createUserInterface() {
        setTitle("Battleship Game");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(1200, 700);
        setLocationRelativeTo(null);

        JPanel mainPanel = new JPanel(new BorderLayout());
        mainPanel.add(createTopPanel(), BorderLayout.NORTH);
        mainPanel.add(createGameBoards(), BorderLayout.CENTER);
        add(mainPanel);
    }

    /**
     * Creates the top panel containing the main status message and the "New Game" button.
     */
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

    /**
     * Creates the main panel that holds both the player's and the opponent's game boards side-by-side.
     */
    private JPanel createGameBoards() {
        JPanel boardsPanel = new JPanel(new GridLayout(1, 2, 20, 0));
        boardsPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        // The top/left board is always displayed from the current user's perspective.
        JPanel board1Panel = createSingleBoard(board1Buttons, "Your Board", true);
        this.player1Label = (JLabel) board1Panel.getComponent(0);
        boardsPanel.add(board1Panel);

        // The bottom/right board always shows the opponent's grid.
        JPanel board2Panel = createSingleBoard(board2Buttons, "Opponent's Board", false);
        this.player2Label = (JLabel) board2Panel.getComponent(0);
        boardsPanel.add(board2Panel);

        return boardsPanel;
    }

    private JPanel createSingleBoard(JButton[][] buttons, String title, boolean isTopBoard) {
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
                buttons[row][col].addActionListener(e -> handleBoardClick(r, c, isTopBoard));
                gridPanel.add(buttons[row][col]);
            }
        }
        boardPanel.add(gridPanel, BorderLayout.CENTER);
        return boardPanel;
    }
    
    /**
     * Manages the initial user interaction flow, prompting the user to either create a new game or join an existing one.
     */
    private void startGameSetup() {
        String[] setupOptions = {"Create Game", "Join Game"};
        int setupChoice = JOptionPane.showOptionDialog(this, "Welcome to Battleship!", "Setup",
            JOptionPane.DEFAULT_OPTION, JOptionPane.INFORMATION_MESSAGE, null, setupOptions, setupOptions[0]);

        if (setupChoice == -1) System.exit(0); // Handle user closing the dialog

        if (setupChoice == 0) { createGameFlow(); } 
        else { joinGameFlow(); }
    }

    /**
     * Manages the sequence of dialogs required for a user to create a new game session.
     * This includes selecting the mode, number of games, and player names.
     */
    private void createGameFlow() {
        // Asks for game mode (PvP or PvE).
        String[] modeOptions = {"Player vs. Bot", "Player vs. Player"};
        int modeChoice = JOptionPane.showOptionDialog(this, "Choose your game mode:", "Create Game",
            JOptionPane.DEFAULT_OPTION, JOptionPane.INFORMATION_MESSAGE, null, modeOptions, modeOptions[0]);

        if (modeChoice == -1) { restartGame(); return; }

        this.isTwoPlayerMode = (modeChoice == 1);
        String mode = this.isTwoPlayerMode ? "vs_player" : "vs_bot";
        
        // Asks for the number of rounds in the match.
        Integer[] gameCounts = {1, 3, 5};
        Integer numGames = (Integer) JOptionPane.showInputDialog(this, "Best of:", "Match Setup",
            JOptionPane.QUESTION_MESSAGE, null, gameCounts, gameCounts[0]);

        if (numGames == null) { restartGame(); return; }

        getPlayerNames(this.isTwoPlayerMode);

        // Calls the connector to send all setup data to the backend.
        String[] createResponse = BattleshipConnector.createGame(mode, this.player1Name, this.player2Name, numGames);
        
        this.gameId = createResponse[0];
        this.playerId = 0; // The user who creates the game is always Player 1 (ID 0).

        if (this.gameId.isEmpty()) {
            JOptionPane.showMessageDialog(this, "Error creating game: " + createResponse[1], "API Error", JOptionPane.ERROR_MESSAGE);
            System.exit(1);
        }

        // If it's a two-player game, show the Game ID so the second player can join.
        if(this.isTwoPlayerMode) {
            JTextArea textArea = new JTextArea("Game created! Share this ID with Player 2:\n" + this.gameId);
            textArea.setEditable(false);
            JOptionPane.showMessageDialog(this, textArea, "Game ID", JOptionPane.INFORMATION_MESSAGE);
        }
        
        // Fetches the initial state from the backend to draw the boards for the first time.
        refreshGameState();
    }

    /**
     * Handles the dialog for a second player to join an existing game session.
     */
    private void joinGameFlow() {
        this.isTwoPlayerMode = true;
        this.gameId = JOptionPane.showInputDialog(this, "Enter the Game ID from Player 1:", "Join Game", JOptionPane.QUESTION_MESSAGE);

        if (this.gameId == null || this.gameId.trim().isEmpty()) { restartGame(); return; }
        
        this.playerId = 1; // The user who joins is always Player 2 (ID 1).
        this.player1Name = "Player 1"; // These will be updated with the actual names from the server.
        this.player2Name = "Player 2";

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
    
    /**
     * A helper method to fetch the latest game state from the server.
     * This is primarily used by the polling timer in two-player mode.
     */
    private void refreshGameState() {
        String jsonResponse = BattleshipConnector.getGameState(this.gameId, this.playerId);
        updateUiFromJson(jsonResponse);
    }

    private void handleBoardClick(int row, int col, boolean isTopBoard) {
        // Clicks on your own board or when it's not your turn are ignored.
        if (isTopBoard || !this.isMyTurn) return;
        
        // Sends the attack coordinates to the backend and updates the UI with the response.
        String jsonResponse = BattleshipConnector.attack(this.gameId, this.playerId, row, col);
        updateUiFromJson(jsonResponse);
    }
    
    /**
     * Starts a timer that periodically calls refreshGameState().
     * This is used in two-player mode to automatically get the opponent's move from the server.
     */
    private void startPolling() {
        // Prevents multiple timers from running simultaneously.
        if (pollingTimer != null && pollingTimer.isRunning()) return;
        pollingTimer = new javax.swing.Timer(3000, e -> refreshGameState());
        pollingTimer.setRepeats(true);
        pollingTimer.start();
    }

    private void updateUiFromJson(String jsonResponseString) {
        try {
            JSONObject responseJson = new JSONObject(jsonResponseString);

            // First, check if the server returned an error and display it to the user.
            if (responseJson.has("error")) {
                JOptionPane.showMessageDialog(this, responseJson.getString("error"), "Error", JOptionPane.ERROR_MESSAGE);
                if (pollingTimer != null) pollingTimer.stop();
                return;
            }

            // Extract the main game state object.
            JSONObject gameState = responseJson.getJSONObject("game_state");

            // Update the client's internal state to determine whose turn it is.
            this.isMyTurn = (gameState.getInt("current_turn") == this.playerId) && !gameState.getBoolean("game_over");

            // Update local name variables from the server, the single source of truth.
            this.player1Name = gameState.getString("player1_name");
            this.player2Name = gameState.getString("player2_name");
        
            // Parse scores and sunk ship counts.
            JSONObject wins = gameState.getJSONObject("wins");
            String p1Score = wins.get("0").toString();
            String p2Score = wins.get("1").toString();
        
            // The sunk counts must be displayed from the correct player's perspective.
            String p1SunkCount = (this.playerId == 0) ? gameState.getString("opponent_sinks") : gameState.getString("your_sinks");
            String p2SunkCount = (this.playerId == 0) ? gameState.getString("your_sinks") : gameState.getString("opponent_sinks");

            // Update the info labels above each board, always showing Player 1 on top and Player 2 on bottom.
            this.player1Label.setText(this.player1Name + " | Score: " + p1Score + " | Sunk: " + p2SunkCount);
            this.player2Label.setText(this.player2Name + " | Score: " + p2Score + " | Sunk: " + p1SunkCount);
        
            // Set the main status message at the top of the window.
            this.statusLabel.setText(gameState.getString("status_message"));

            // Redraw both boards using the new grid data from the server.
            updateBoard(board1Buttons, gameState.getJSONArray("your_board"));
            updateBoard(board2Buttons, gameState.getJSONArray("opponent_board"));

            // If a match winner is declared, show a final message and stop the game.
            if (!gameState.isNull("match_winner")) {
                this.isMyTurn = false;
                if(pollingTimer != null) pollingTimer.stop();
                String winnerName = gameState.getInt("match_winner") == 0 ? this.player1Name : this.player2Name;
                JOptionPane.showMessageDialog(this, "Match Over! Winner is " + winnerName, "Match Over", JOptionPane.INFORMATION_MESSAGE);
            // In two-player mode, manage the polling timer based on whose turn it is.
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

    // Updates the visual appearance of a single game board (colors, icons, text) based on data from the server.
    private void updateBoard(JButton[][] buttons, JSONArray boardData) {
        for (int r = 0; r < BOARD_SIZE; r++) {
            JSONArray boardRow = boardData.getJSONArray(r);
            for (int c = 0; c < BOARD_SIZE; c++) {
                String cell = boardRow.getString(c);
                buttons[r][c].setIcon(null);
                buttons[r][c].setText("");
                switch (cell) {
                    case "S": // Your own, untouched ship
                        buttons[r][c].setBackground(Color.decode("#000000"));
                        buttons[r][c].setText("");
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
                        buttons[r][c].setBackground(Color.decode("#d3d3d3"));
                        buttons[r][c].setText("");
                        break;
                }
            }
        }
    }
    
    /**
     * Closes the current game window and starts a fresh instance of the application.
     * This is triggered by the "New Game" button.
     */
    private void restartGame() {
        if(pollingTimer != null) pollingTimer.stop();
        this.dispose();
        SwingUtilities.invokeLater(() -> new Game().setVisible(true));
    }

    /**
     * The main entry point for the application.
     * It creates and shows the game window on the Event Dispatch Thread for thread safety.
     */
    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new Game().setVisible(true));
    }
}
