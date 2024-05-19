import com.itextpdf.text.DocumentException;

import java.io.IOException;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.List;

public class Main {
    public static void main(String[] args) {
        // Load user data from JSON
        DBManager dbManager = new DBManager("users.json");

        // Demonstrate login
        LoginService loginService = new LoginService(dbManager);
        boolean loginSuccess = loginService.login("user@vulnerableapp.com", "weakpass");

        // Generate a report listing all users and calculate hash
        List<String> userData = new ArrayList<>();
        dbManager.getAllUsers().forEach(user -> userData.add(user.getEmail() + " - " + user.getPassword()));

        if(loginSuccess) {
            System.out.println("Login Successful. Generating report.");

            Report report = new Report();
            try {
                report.generatePDFAndHash("UserReport.pdf", userData);
                System.out.println("PDF and hash generated successfully.");
            } catch (DocumentException | IOException | NoSuchAlgorithmException e) {
                e.printStackTrace();
            }
        } else {
            System.out.println("Login Unsuccessful");
        }
    }
}
