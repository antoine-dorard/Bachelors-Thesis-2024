import main

def test_summarize():
    summary = main.Summary(api_key="a")
    
    full_summary = summary.summarize_classes_and_methods("vulnerableapp/DBManager.java")
    
    
def test_extract_java_methods():
    file = "vulnerableapp/DBManager.java"
    
    with open(file, 'r') as f:
        java_code = f.read()
        
    methods = main.extract_java_methods(java_code)
    assert methods[0][0] == "DBManager"
    assert methods[0][1] == "loadUsers"
    assert methods[0][2] == \
    """void loadUsers(String filename) {
        try (Reader reader = new FileReader(filename)) {
            Type type = new TypeToken<List<User>>(){}.getType();
            List<User> userList = new Gson().fromJson(reader, type);
            userList.forEach(user -> users.put(user.getEmail(), user.getPassword()));
        } catch (Exception e) {
            e.printStackTrace();
        }
    }"""
    
    assert methods[1][0] == "DBManager"
    assert methods[1][1] == "checkCredentials"
    assert methods[1][2] == \
    """boolean checkCredentials(String email, String encryptedPassword) {
        String storedEncryptedPassword = users.get(email);
        return storedEncryptedPassword != null && storedEncryptedPassword.equals(encryptedPassword);
    }"""
    
    assert methods[2][0] == "DBManager"
    assert methods[2][1] == "getAllUsers"
    assert methods[2][2] == \
    """List<User> getAllUsers() {
        return users.entrySet().stream()
                .map(entry -> new User(entry.getKey(), entry.getValue()))
                .collect(Collectors.toList());
    }"""
    
    assert methods[3][0] == "User"
    assert methods[3][1] == "getEmail"
    assert methods[3][2] == \
    """String getEmail() {
            return email;
        }"""
    
    assert methods[4][0] == "User"
    assert methods[4][1] == "getPassword"
    assert methods[4][2] == \
    """String getPassword() {
            return password;
        }"""
    
    
    code1 = \
    """public class User { private String email; private String password; public User(String email, String password) { this.email = email; this.password = password; \
    } public String getEmail() { return email; } sss
    public String getPassword() {
        return password; }
}"""
    code2 = \
    """public class User { private String email; private String password; public User(String email, String password) { this.email = email; this.password = password; \
    } public String getEmail() { 
        return email; 
    }
    public String getPassword() {
        return password; }
}"""

    code3 = \
    """public class User { private String email; private String password; public User(String email, String password) 
    { this.email = email; this.password = password; } public String getEmail() { return email; } sss"""

    code4 = \
    """public class User { private String email; private String password; public User(String email, String password){ this.email = email; this.password = password; } }"""
    
    code5 = \
    """public class User { private String email; private String password; public User(String email, String password) 
    
    { this.email = email; 
    
    this.password = password; 
    
    } public String getEmail() { return email; } sss"""
    
    assert "\n".join(main.extract_java_methods_body(code1.splitlines(), 1, 68)) == \
    """public User(String email, String password) { this.email = email; this.password = password;     } """
    
    assert "\n".join(main.extract_java_methods_body(code2.splitlines(), 1, 68)) == \
    """public User(String email, String password) { this.email = email; this.password = password;     } """
    
    assert "\n".join(main.extract_java_methods_body(code3.splitlines(), 1, 68)) == \
    """public User(String email, String password) 
    { this.email = email; this.password = password; } """
    
    assert "\n".join(main.extract_java_methods_body(code4.splitlines(), 1, 68)) == \
        """public User(String email, String password){ this.email = email; this.password = password; } """
        
    assert "\n".join(main.extract_java_methods_body(code5.splitlines(), 1, 68)) == \
        """public User(String email, String password) 
    { this.email = email; 
    
    this.password = password; 
    
    } """
    
    print("All tests passed!")
    
if __name__ == '__main__':
    # test_summarize()
    test_extract_java_methods()