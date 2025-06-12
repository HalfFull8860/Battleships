import java.io.*;
import java.net.*;
import org.json.JSONObject;

public class BattleshipConnector {

    // Send a request to the backend to create the game
    public static String[] createGame(String gamemode, String player1Name, String player2Name, int numGames) {
        try {
            URL url = new URL("http://127.0.0.1:5001/game");
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json; utf-8");
            conn.setRequestProperty("Accept", "application/json");
            conn.setDoOutput(true);

            // Create JSON payload
            JSONObject jsonInput = new JSONObject();
            jsonInput.put("mode", gamemode);
            jsonInput.put("player1_name", player1Name);
            jsonInput.put("player2_name", player2Name);
            jsonInput.put("number_of_games", numGames);

            // Send request
            try (OutputStream os = conn.getOutputStream()) {
                byte[] input = jsonInput.toString().getBytes("utf-8");
                System.out.println("Message sent to server:");
                System.out.println(jsonInput.toString());
                os.write(input, 0, input.length);
            }

            // Read response
            StringBuilder response = new StringBuilder();
            try (BufferedReader br = new BufferedReader(
                    new InputStreamReader(conn.getInputStream(), "utf-8"))) {
                String responseLine;
                while ((responseLine = br.readLine()) != null) {
                    response.append(responseLine.trim());
                }
                System.out.println("Response from server:");
                System.out.println(response.toString());
            }

            // Parse JSON response
            JSONObject jsonResponse = new JSONObject(response.toString());
            String gameid = jsonResponse.optString("game_id", "");
            String message = jsonResponse.optString("message", "");
            String mode = jsonResponse.optString("mode", "");
            String numberOfGames = jsonResponse.optString("number_of_games", "");
            String p1name = jsonResponse.optString("player1_name", "");
            String p2name = jsonResponse.optString("player2_name", "");
            String p1id = jsonResponse.optString("player_1_id", "");
            String p2id = jsonResponse.optString("player_2_id", "");

            return new String[] { gameid, message };

        } catch (Exception e) {
            e.printStackTrace();
            return new String[] { "", "Error: " + e.getMessage() };
        }
    }

    // Add this new method
    public static String getGameState(String gameId, int playerId) {
        try {
            // Note the construction of the URL with the gameId and a query parameter
            URL url = new URL("http://127.0.0.1:5001/game/" + gameId + "?player_id=" + playerId);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            conn.setRequestProperty("Accept", "application/json");

            if (conn.getResponseCode() != 200) {
                return "{\"error\": \"Failed : HTTP error code : " + conn.getResponseCode() + "\"}";
            }

            // Read response
            StringBuilder response = new StringBuilder();
            try (BufferedReader br = new BufferedReader(
                    new InputStreamReader(conn.getInputStream(), "utf-8"))) {
                String responseLine;
                while ((responseLine = br.readLine()) != null) {
                    response.append(responseLine.trim());
                }
            }
            return response.toString();

        } catch (Exception e) {
            e.printStackTrace();
            return "{\"error\": \"" + e.getMessage() + "\"}";
        }
    }

    // Add this new method
    public static String attack(String gameId, int playerId, int row, int col) {
        HttpURLConnection conn = null; // Defined outside the try block
        try {
            URL url = new URL("http://127.0.0.1:5001/game/" + gameId + "/attack");
            conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json; utf-8");
            conn.setRequestProperty("Accept", "application/json");
            conn.setDoOutput(true);

            // Create and send JSON payload
            JSONObject jsonInput = new JSONObject();
            jsonInput.put("player_id", playerId);
            jsonInput.put("row", row);
            jsonInput.put("col", col);

            try (OutputStream os = conn.getOutputStream()) {
                byte[] input = jsonInput.toString().getBytes("utf-8");
                os.write(input, 0, input.length);
            }

            // NEW: Check the response code
            int responseCode = conn.getResponseCode();
        
            // Determine which stream to read from (input stream for success, error stream for failure)
            InputStream stream = (responseCode >= 400) ? conn.getErrorStream() : conn.getInputStream();
        
            // Read the response from the appropriate stream
            StringBuilder response = new StringBuilder();
            try (BufferedReader br = new BufferedReader(new InputStreamReader(stream, "utf-8"))) {
                String responseLine;
                while ((responseLine = br.readLine()) != null) {
                    response.append(responseLine.trim());
                }
            }
            return response.toString();

        } catch (Exception e) {
            e.printStackTrace();
            return "{\"error\": \"" + e.getMessage() + "\"}";
        } finally {
            if(conn != null) {
                conn.disconnect();
            }
        }
    }
}