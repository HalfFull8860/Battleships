import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import javax.swing.*;

// Driver Class
public class Mainer {
    // main function
    public static void main(String[] args)
    {

        String ip = "127.0.0.1:5000";
        String path = "/";
        String urlString = "http://" + ip + path;

        String result = "Default result";

        try {
            URL url = new URL(urlString);
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();

            // Optional: set Host header if needed
            connection.setRequestProperty("Host", "example.com");

            connection.setRequestMethod("GET");

            int responseCode = connection.getResponseCode();
            System.out.println("Response Code: " + responseCode);

            BufferedReader in = new BufferedReader(
                new InputStreamReader(connection.getInputStream())
            );

            String inputLine;
            StringBuilder response = new StringBuilder();

            while ((inputLine = in.readLine()) != null) {
                response.append(inputLine).append("\n");
            }
            in.close();

            result = response.toString();

        } catch (IOException e) {
            e.printStackTrace();
        }

        // Create a new JFrame
        JFrame frame = new JFrame("Battleships");

        // Create a label
        JLabel label
            = new JLabel(result);

        // Add the label to the frame
        frame.add(label);

        // Set frame properties
        frame.setSize(300,
                      200); // Set the size of the frame

        // Close operation
        frame.setDefaultCloseOperation(
            JFrame.EXIT_ON_CLOSE);

        // Make the frame visible
        frame.setVisible(true);
    }
}