import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public class Game extends JFrame {
    private static final int BOARD_SIZE = 10;
    private static final int GAME_TIME = 120;
    
    // Ship configuration
    private static final int[] SHIP_SIZES = {5, 4, 3, 2};
    private static final String[] SHIP_NAMES = {"Carrier", "Battleship", "Cruiser", "Destroyer"};
    
    // Game state variables
    private boolean isOnePlayer = true;
    private boolean isPlacementPhase = true;
    private boolean isPlayer1Turn = true;
    private int currentShipIndex = 0;
    private boolean isHorizontal = true;
    private int placementPlayer = 1;
    private int timeLeft = GAME_TIME;
    
    // Player information
    private String player1Name = "Player 1";
    private String player2Name = "Player 2";
    
    // Game boards
    private final int[][] player1Board = new int[BOARD_SIZE][BOARD_SIZE];
    private final int[][] player2Board = new int[BOARD_SIZE][BOARD_SIZE];
    private final int[][] player1Attacks = new int[BOARD_SIZE][BOARD_SIZE];
    private final int[][] player2Attacks = new int[BOARD_SIZE][BOARD_SIZE];
    
    // Ships to place
    private final List<Integer> player1Ships = new ArrayList<>();
    private final List<Integer> player2Ships = new ArrayList<>();
    
    // UI Components
    private JPanel mainPanel;
    private final JButton[][] board1Buttons = new JButton[BOARD_SIZE][BOARD_SIZE];
    private final JButton[][] board2Buttons = new JButton[BOARD_SIZE][BOARD_SIZE];
    private JLabel statusLabel;
    private JLabel timerLabel;
    private JLabel player1Label;
    private JLabel player2Label;
    private JButton orientationButton;
    private JLabel shipLabel;
    private javax.swing.Timer gameTimer;
    
    public Game() {
        initializeGame();
        createUserInterface();
        startGameSetup();
    }
    
    private void initializeGame() {
        // Initialize ship lists
        for (int size : SHIP_SIZES) {
            player1Ships.add(size);
            player2Ships.add(size);
        }
        
        // Setup game timer
        gameTimer = new javax.swing.Timer(1000, new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                timeLeft--;
                updateTimerDisplay();
                if (timeLeft <= 0) {
                    String winner = isPlayer1Turn ? player2Name : player1Name;
                    endGame("Time's up! " + winner + " wins!");
                }
            }
        });
    }
    
    private void createUserInterface() {
        setTitle("Battleship Game");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(1000, 700);
        setLocationRelativeTo(null);
        
        mainPanel = new JPanel(new BorderLayout());
        
        createTopPanel();
        createGameBoards();
        
        add(mainPanel);
    }
    
    private void createTopPanel() {
        JPanel topPanel = new JPanel(new BorderLayout());
        
        // Status label
        statusLabel = new JLabel("Welcome to Battleship!", SwingConstants.CENTER);
        statusLabel.setFont(new Font("Arial", Font.BOLD, 16));
        
        // Control panel
        JPanel controlPanel = new JPanel(new FlowLayout());
        
        timerLabel = new JLabel("Time: 2:00");
        timerLabel.setFont(new Font("Arial", Font.BOLD, 14));
        
        JButton newGameButton = new JButton("New Game");
        newGameButton.addActionListener(e -> restartGame());
        
        orientationButton = new JButton("Horizontal");
        orientationButton.addActionListener(e -> toggleShipOrientation());
        orientationButton.setVisible(false);
        
        shipLabel = new JLabel("");
        shipLabel.setFont(new Font("Arial", Font.BOLD, 12));
        shipLabel.setVisible(false);
        
        controlPanel.add(timerLabel);
        controlPanel.add(newGameButton);
        controlPanel.add(orientationButton);
        controlPanel.add(shipLabel);
        
        topPanel.add(statusLabel, BorderLayout.CENTER);
        topPanel.add(controlPanel, BorderLayout.EAST);
        
        mainPanel.add(topPanel, BorderLayout.NORTH);
    }
    
    private void createGameBoards() {
        JPanel boardsPanel = new JPanel(new GridLayout(1, 2, 20, 0));
        
        // Create Player 1 board
        JPanel board1Panel = createSingleBoard(board1Buttons, "Player 1's Board", true);
        player1Label = (JLabel) board1Panel.getComponent(0);
        
        // Create Player 2 board
        JPanel board2Panel = createSingleBoard(board2Buttons, "Player 2's Board", false);
        player2Label = (JLabel) board2Panel.getComponent(0);
        
        boardsPanel.add(board1Panel);
        boardsPanel.add(board2Panel);
        
        mainPanel.add(boardsPanel, BorderLayout.CENTER);
    }
    
    private JPanel createSingleBoard(JButton[][] buttons, String title, boolean isPlayer1Board) {
        JPanel boardPanel = new JPanel(new BorderLayout());
        
        JLabel titleLabel = new JLabel(title, SwingConstants.CENTER);
        titleLabel.setFont(new Font("Arial", Font.BOLD, 14));
        boardPanel.add(titleLabel, BorderLayout.NORTH);
        
        JPanel gridPanel = new JPanel(new GridLayout(BOARD_SIZE, BOARD_SIZE, 1, 1));
        
        for (int row = 0; row < BOARD_SIZE; row++) {
            for (int col = 0; col < BOARD_SIZE; col++) {
                buttons[row][col] = new JButton();
                buttons[row][col].setPreferredSize(new Dimension(35, 35));
                buttons[row][col].setBackground(Color.CYAN);
                
                final int r = row;
                final int c = col;
                final boolean isP1 = isPlayer1Board;
                
                buttons[row][col].addActionListener(e -> handleBoardClick(r, c, isP1));
                
                gridPanel.add(buttons[row][col]);
            }
        }
        
        boardPanel.add(gridPanel, BorderLayout.CENTER);
        return boardPanel;
    }
    
    private void startGameSetup() {
        String[] options = {"1 Player (vs AI)", "2 Players"};
        int choice = JOptionPane.showOptionDialog(
            this,
            "Choose game mode:",
            "Battleship Setup",
            JOptionPane.YES_NO_OPTION,
            JOptionPane.QUESTION_MESSAGE,
            null,
            options,
            options[0]
        );
        
        if (choice == -1) { // User closed dialog
            System.exit(0);
            return;
        }
        
        isOnePlayer = (choice == 0);
        
        // Get player names
        getPlayerNames();
        
        // Start ship placement
        startShipPlacement();
    }
    
    private void getPlayerNames() {
        player1Name = JOptionPane.showInputDialog(
            this,
            "Enter Player 1 name:",
            "Player Setup",
            JOptionPane.QUESTION_MESSAGE
        );
        
        if (player1Name == null || player1Name.trim().isEmpty()) {
            player1Name = "Player 1";
        }
        
        if (isOnePlayer) {
            player2Name = "AI";
        } else {
            player2Name = JOptionPane.showInputDialog(
                this,
                "Enter Player 2 name:",
                "Player Setup",
                JOptionPane.QUESTION_MESSAGE
            );
            
            if (player2Name == null || player2Name.trim().isEmpty()) {
                player2Name = "Player 2";
            }
        }
    }
    
    private void startShipPlacement() {
        isPlacementPhase = true;
        placementPlayer = 1;
        currentShipIndex = 0;
        
        updateBoardLabels();
        updateStatusMessage();
        updateShipInformation();
        
        orientationButton.setVisible(true);
        shipLabel.setVisible(true);
    }
    
    private void handleBoardClick(int row, int col, boolean isPlayer1Board) {
        if (isPlacementPhase) {
            handleShipPlacement(row, col, isPlayer1Board);
        } else {
            handleAttackMove(row, col, isPlayer1Board);
        }
    }
    
    private void handleShipPlacement(int row, int col, boolean isPlayer1Board) {
        // Only allow placement on current player's board
        if ((placementPlayer == 1 && !isPlayer1Board) || (placementPlayer == 2 && isPlayer1Board)) {
            return;
        }
        
        List<Integer> currentPlayerShips = (placementPlayer == 1) ? player1Ships : player2Ships;
        if (currentPlayerShips.isEmpty()) return;
        
        int shipSize = currentPlayerShips.get(currentShipIndex);
        int[][] currentBoard = (placementPlayer == 1) ? player1Board : player2Board;
        
        if (canPlaceShip(currentBoard, row, col, shipSize, isHorizontal)) {
            placeShip(currentBoard, row, col, shipSize, isHorizontal);
            currentPlayerShips.remove(currentShipIndex);
            currentShipIndex = 0;
            
            updateBoardDisplay(placementPlayer == 1);
            
            if (currentPlayerShips.isEmpty()) {
                handlePlayerFinishedPlacement();
            } else {
                updateShipInformation();
            }
        }
    }
    
    private void handlePlayerFinishedPlacement() {
        if (placementPlayer == 1) {
            if (isOnePlayer) {
                placeAIShips();
                startBattlePhase();
            } else {
                placementPlayer = 2;
                currentShipIndex = 0;
                updateStatusMessage();
                updateShipInformation();
            }
        } else {
            startBattlePhase();
        }
    }
    
    private void handleAttackMove(int row, int col, boolean isPlayer1Board) {
        // Player 1 attacks Player 2's board, Player 2 attacks Player 1's board
        boolean isValidTarget = (isPlayer1Turn && !isPlayer1Board) || (!isPlayer1Turn && isPlayer1Board);
        if (!isValidTarget) return;
        
        int[][] targetBoard = isPlayer1Board ? player1Board : player2Board;
        int[][] attackBoard = isPlayer1Turn ? player1Attacks : player2Attacks;
        
        if (attackBoard[row][col] != 0) return; // Already attacked this position
        
        boolean isHit = (targetBoard[row][col] == 1);
        attackBoard[row][col] = isHit ? 2 : 3;
        
        String attackerName = isPlayer1Turn ? player1Name : player2Name;
        statusLabel.setText(attackerName + (isHit ? " HIT!" : " MISSED!"));
        
        updateBoardDisplay(!isPlayer1Board);
        
        if (checkForWin(attackBoard)) {
            endGame(attackerName + " wins!");
            return;
        }
        
        switchTurns();
        
        if (isOnePlayer && !isPlayer1Turn) {
            performAIAttack();
        }
    }
    
    private void performAIAttack() {
        javax.swing.Timer aiDelay = new javax.swing.Timer(1000, new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                executeAIMove();
                ((javax.swing.Timer)e.getSource()).stop();
            }
        });
        aiDelay.setRepeats(false);
        aiDelay.start();
    }
    
    private void executeAIMove() {
        Random random = new Random();
        int row, col;
        
        do {
            row = random.nextInt(BOARD_SIZE);
            col = random.nextInt(BOARD_SIZE);
        } while (player2Attacks[row][col] != 0);
        
        boolean isHit = (player1Board[row][col] == 1);
        player2Attacks[row][col] = isHit ? 2 : 3;
        
        statusLabel.setText(player2Name + (isHit ? " HIT!" : " MISSED!"));
        updateBoardDisplay(true);
        
        if (checkForWin(player2Attacks)) {
            endGame(player2Name + " wins!");
            return;
        }
        
        switchTurns();
    }
    
    private boolean canPlaceShip(int[][] board, int row, int col, int size, boolean horizontal) {
        for (int i = 0; i < size; i++) {
            int r = horizontal ? row : row + i;
            int c = horizontal ? col + i : col;
            
            if (r >= BOARD_SIZE || c >= BOARD_SIZE || board[r][c] != 0) {
                return false;
            }
        }
        return true;
    }
    
    private void placeShip(int[][] board, int row, int col, int size, boolean horizontal) {
        for (int i = 0; i < size; i++) {
            int r = horizontal ? row : row + i;
            int c = horizontal ? col + i : col;
            board[r][c] = 1;
        }
    }
    
    private void placeAIShips() {
        Random random = new Random();
        
        for (int shipSize : SHIP_SIZES) {
            boolean placed = false;
            int attempts = 0;
            
            while (!placed && attempts < 1000) {
                int row = random.nextInt(BOARD_SIZE);
                int col = random.nextInt(BOARD_SIZE);
                boolean horizontal = random.nextBoolean();
                
                if (canPlaceShip(player2Board, row, col, shipSize, horizontal)) {
                    placeShip(player2Board, row, col, shipSize, horizontal);
                    placed = true;
                }
                attempts++;
            }
        }
        player2Ships.clear();
    }
    
    private void startBattlePhase() {
        isPlacementPhase = false;
        isPlayer1Turn = true;
        timeLeft = GAME_TIME;
        
        orientationButton.setVisible(false);
        shipLabel.setVisible(false);
        
        updateBoardLabels();
        statusLabel.setText("Battle begins! " + player1Name + "'s turn");
        gameTimer.start();
        
        updateBoardDisplay(true);
        updateBoardDisplay(false);
    }
    
    private boolean checkForWin(int[][] attackBoard) {
        int hitCount = 0;
        for (int i = 0; i < BOARD_SIZE; i++) {
            for (int j = 0; j < BOARD_SIZE; j++) {
                if (attackBoard[i][j] == 2) hitCount++;
            }
        }
        
        int totalShipCells = 0;
        for (int size : SHIP_SIZES) {
            totalShipCells += size;
        }
        
        return hitCount == totalShipCells;
    }
    
    private void switchTurns() {
        isPlayer1Turn = !isPlayer1Turn;
        timeLeft = GAME_TIME;
        
        String currentPlayerName = isPlayer1Turn ? player1Name : player2Name;
        statusLabel.setText(currentPlayerName + "'s turn");
    }
    
    private void endGame(String message) {
        if (gameTimer.isRunning()) {
            gameTimer.stop();
        }
        
        statusLabel.setText(message);
        
        int choice = JOptionPane.showConfirmDialog(
            this,
            message + "\nWould you like to play again?",
            "Game Over",
            JOptionPane.YES_NO_OPTION
        );
        
        if (choice == JOptionPane.YES_OPTION) {
            restartGame();
        } else {
            System.exit(0);
        }
    }
    
    private void toggleShipOrientation() {
        isHorizontal = !isHorizontal;
        orientationButton.setText(isHorizontal ? "Horizontal" : "Vertical");
    }
    
    private void updateBoardDisplay(boolean isPlayer1Board) {
        JButton[][] buttons = isPlayer1Board ? board1Buttons : board2Buttons;
        int[][] board = isPlayer1Board ? player1Board : player2Board;
        int[][] attacks = isPlayer1Board ? player2Attacks : player1Attacks;
        
        for (int i = 0; i < BOARD_SIZE; i++) {
            for (int j = 0; j < BOARD_SIZE; j++) {
                Color cellColor = Color.CYAN; // Default water color
                
                if (isPlacementPhase) {
                    if (board[i][j] == 1) {
                        cellColor = Color.GRAY; // Ship
                    }
                } else {
                    if (isPlayer1Board) {
                        // Own board - show ships and damage
                        if (board[i][j] == 1) {
                            cellColor = (attacks[i][j] == 2) ? Color.RED : Color.GRAY;
                        } else if (attacks[i][j] == 3) {
                            cellColor = Color.BLUE; // Miss
                        }
                    } else {
                        // Enemy board - only show hits and misses
                        if (attacks[i][j] == 2) {
                            cellColor = Color.RED; // Hit
                        } else if (attacks[i][j] == 3) {
                            cellColor = Color.BLUE; // Miss
                        }
                    }
                }
                
                buttons[i][j].setBackground(cellColor);
            }
        }
    }
    
    private void updateBoardLabels() {
        if (isPlacementPhase) {
            player1Label.setText(player1Name + " - Place Ships");
            player2Label.setText(player2Name + " - Place Ships");
        } else {
            player1Label.setText(player1Name + "'s Ships");
            player2Label.setText(isOnePlayer ? (player2Name + "'s Waters") : (player2Name + "'s Waters"));
        }
    }
    
    private void updateStatusMessage() {
        if (isPlacementPhase) {
            String currentPlayerName = (placementPlayer == 1) ? player1Name : player2Name;
            statusLabel.setText(currentPlayerName + ": Place your ships");
        } else {
            String currentPlayerName = isPlayer1Turn ? player1Name : player2Name;
            statusLabel.setText(currentPlayerName + "'s turn");
        }
    }
    
    private void updateShipInformation() {
        if (isPlacementPhase) {
            List<Integer> ships = (placementPlayer == 1) ? player1Ships : player2Ships;
            if (!ships.isEmpty() && currentShipIndex < ships.size()) {
                int shipSize = ships.get(currentShipIndex);
                String shipName = SHIP_NAMES[shipSize - 2]; // Convert size to name index
                shipLabel.setText("Place: " + shipName + " (" + shipSize + " cells)");
            }
        }
    }
    
    private void updateTimerDisplay() {
        int minutes = timeLeft / 60;
        int seconds = timeLeft % 60;
        timerLabel.setText(String.format("Time: %d:%02d", minutes, seconds));
    }
    
    private void restartGame() {
        if (gameTimer.isRunning()) {
            gameTimer.stop();
        }
        
        // Reset all game state
        isPlacementPhase = true;
        isPlayer1Turn = true;
        placementPlayer = 1;
        currentShipIndex = 0;
        isHorizontal = true;
        timeLeft = GAME_TIME;
        
        // Clear all boards
        clearBoard(player1Board);
        clearBoard(player2Board);
        clearBoard(player1Attacks);
        clearBoard(player2Attacks);
        
        // Reset ship lists
        player1Ships.clear();
        player2Ships.clear();
        for (int size : SHIP_SIZES) {
            player1Ships.add(size);
            player2Ships.add(size);
        }
        
        // Reset UI
        updateBoardDisplay(true);
        updateBoardDisplay(false);
        
        // Start new game
        startGameSetup();
    }
    
    private void clearBoard(int[][] board) {
        for (int i = 0; i < BOARD_SIZE; i++) {
            for (int j = 0; j < BOARD_SIZE; j++) {
                board[i][j] = 0;
            }
        }
    }
    
    public static void main(String[] args) {
        SwingUtilities.invokeLater(new Runnable() {
            @Override
            public void run() {
                new Game().setVisible(true);
            }
        });
    }
}