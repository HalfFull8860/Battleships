public class Mainer {
    // main function
    public static void main(String[] args)
    {
        try {
            Thread.sleep(5000);
        } catch (InterruptedException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        } // Sleep for 1 second to ensure the backend is ready
        String[] response = BattleshipConnector.createGame("vs_bot", "Sergio", "Bot", 1);
        System.out.println(response[0]);
    }
}