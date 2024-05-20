import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import java.io.FileReader;
import java.io.Reader;
import java.lang.reflect.Type;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;


public class DBManager {
    private Map<String, String> users = new HashMap<>();

    public DBManager(String filename) {
        loadUsers(filename);
    }

    private void loadUsers(String filename) {
        try (Reader reader = new FileReader(filename)) {
            Type type = new TypeToken<List<User>>(){}.getType();
            List<User> userList = new Gson().fromJson(reader, type);
            userList.forEach(user -> users.put(user.getEmail(), user.getPassword()));
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public boolean checkCredentials(String email, String encryptedPassword) {
        String storedEncryptedPassword = users.get(email);
        return storedEncryptedPassword != null && storedEncryptedPassword.equals(encryptedPassword);
    }

    public List<User> getAllUsers() {
        return users.entrySet().stream()
                .map(entry -> new User(entry.getKey(), entry.getValue()))
                .collect(Collectors.toList());
    }

    public class User {
        private String email;
        private String password;

        public User(String email, String password) {
            this.email = email;
            this.password = password;
        }

        public String getEmail() {
            return email;
        }

        public String getPassword() {
            return password;
        }
    }
}