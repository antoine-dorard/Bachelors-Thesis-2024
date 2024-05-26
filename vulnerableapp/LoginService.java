public class LoginService {
    private DBManager dbManager;

    public LoginService(DBManager dbManager) {
        this.dbManager = dbManager;
    }

    public boolean login(String email, String password) {
        String hashedPassword = HashingUtils.hashSHA256(password);
        System.out.println(hashedPassword);
        
        return dbManager.checkCredentials(email, hashedPassword);
    }
}
