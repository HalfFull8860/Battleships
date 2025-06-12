import java.io.*;
import java.net.*;
import org.json.JSONObject;

/**
 * A utility class with static methods to handle all communication with the Python backend API.
 * This class is responsible for sending HTTP requests and handling the responses.
 */
public class BattleshipConnector {

    // Send a request to the backend to create the game
    public static String[] createGame(String gamemode, String player1Name, String player2Name, int numGames) {
        try {
            // Establishes a connection to the /game endpoint on the server.
            URL url = new URL("http://127.0.0.1:5001/game");
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json; utf-8");
            conn.setRequestProperty("Accept", "application/json");
            conn.setDoOutput(true);

            // Constructs the JSON object with all the necessary game setup details.
            JSONObject jsonInput = new JSONObject();
            jsonInput.put("mode", gamemode);
            jsonInput.put("player1_name", player1Name);
            jsonInput.put("player2_name", player2Name);
            jsonInput.put("number_of_games", numGames);

            // Writes the JSON payload to the request's output stream.
            try (OutputStream os = conn.getOutputStream()) {
                byte[] input = jsonInput.toString().getBytes("utf-8");
                System.out.println("Message sent to server:");
                System.out.println(jsonInput.toString());
                os.write(input, 0, input.length);
            }

            // Reads the server's response from the input stream.
            // This block assumes a successful response (e.g., HTTP 200 or 201).
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

            // Parses the JSON response to extract only the essential information needed by the client.
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
            // In case of any connection or I/O error, print the stack trace and return an error message.
            e.printStackTrace();
            return new String[] { "", "Error: " + e.getMessage() };
        }
    }

    public static String getGameState(String gameId, int playerId) {
        try {
            // Construct the URL, including the gameId as a path variable and playerId as a query parameter.
            URL url = new URL("http://127.0.0.1:5001/game/" + gameId + "?player_id=" + playerId);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            conn.setRequestProperty("Accept", "application/json");

            if (conn.getResponseCode() != 200) {
                return "{\"error\": \"Failed : HTTP error code : " + conn.getResponseCode() + "\"}";
            }

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

    public static String attack(String gameId, int playerId, int row, int col) {
        HttpURLConnection conn = null;
        try {
            // Establish a connection to the /attack endpoint for the specific game.
            URL url = new URL("http://127.0.0.1:5001/game/" + gameId + "/attack");
            conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json; utf-8");
            conn.setRequestProperty("Accept", "application/json");
            conn.setDoOutput(true);

            // Construct the JSON payload with the attack coordinates.
            JSONObject jsonInput = new JSONObject();
            jsonInput.put("player_id", playerId);
            jsonInput.put("row", row);
            jsonInput.put("col", col);

            // Write the JSON payload to the request's output stream.
            try (OutputStream os = conn.getOutputStream()) {
                byte[] input = jsonInput.toString().getBytes("utf-8");
                os.write(input, 0, input.length);
            }

            // Check the HTTP response code to determine if the request was successful.
            int responseCode = conn.getResponseCode();
        
            // Read from the appropriate stream: InputStream for success (e.g., 200) or ErrorStream for failure (e.g., 400).
            InputStream stream = (responseCode >= 400) ? conn.getErrorStream() : conn.getInputStream();
        
            // Read the full response, which could be a success JSON object or an error JSON object.
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
            // Ensure the connection is always closed after the request is complete.
            if(conn != null) {
                conn.disconnect();
            }
        }
    }
}