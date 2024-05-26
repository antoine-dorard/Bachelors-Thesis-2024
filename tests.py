import main

def test_summarize():
    summary = main.Summary(api_key="a")
    
    full_summary = summary.summarize_classes_and_methods("vulnerableapp/DBManager.java")
    

def test_extract_java_methods(verbose=True):
    file = "vulnerableapp/DBManager.java.test"
    
    with open(file, 'r') as f:
        java_code = f.read()
        
    class_objects = main.extract_and_summarize(java_code, None, include_summary=False)
    
    for class_el in class_objects:
        if class_el.name == "DBManager":
            for method_el in class_el.methods:
                if method_el.name == "loadUsers":
                    assert method_el.code == \
    """void loadUsers(String filename) {
        try (Reader reader = new FileReader(filename)) {
            Type type = new TypeToken<List<User>>(){}.getType();
            List<User> userList = new Gson().fromJson(reader, type);
            userList.forEach(user -> users.put(user.getEmail(), user.getPassword()));
        } catch (Exception e) {
            e.printStackTrace();
        }
    }"""
                if method_el.name == "checkCredentials":
                    assert method_el.code == \
    """boolean checkCredentials(String email, String hashedPassword) {
        String storedhashedPassword = users.get(email);
        return storedhashedPassword != null && storedhashedPassword.equals(hashedPassword);
    }"""
                if method_el.name == "getAllUsers":
                    assert method_el.code == \
    """List<User> getAllUsers() {
        return users.entrySet().stream()
                .map(entry -> new User(entry.getKey(), entry.getValue()))
                .collect(Collectors.toList());
    }"""
    
                
        if class_el.name == "User":
            for method_el in class_el.methods:
                if method_el.name == "getEmail":
                    assert method_el.code == \
    """String getEmail() {
            return email;
        }"""
                
                if method_el.name == "getPassword":
                    assert method_el.code == \
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
    
    assert "\n".join(main.extract_java_methods_body(code1.splitlines(), 1, 68)[0]) == \
    """public User(String email, String password) { this.email = email; this.password = password;     }"""
    
    assert "\n".join(main.extract_java_methods_body(code2.splitlines(), 1, 68)[0]) == \
    """public User(String email, String password) { this.email = email; this.password = password;     }"""
    
    assert "\n".join(main.extract_java_methods_body(code3.splitlines(), 1, 68)[0]) == \
    """public User(String email, String password) 
    { this.email = email; this.password = password; }"""
    
    assert "\n".join(main.extract_java_methods_body(code4.splitlines(), 1, 68)[0]) == \
        """public User(String email, String password){ this.email = email; this.password = password; }"""
        
    assert "\n".join(main.extract_java_methods_body(code5.splitlines(), 1, 68)[0]) == \
        """public User(String email, String password) 
    { this.email = email; 
    
    this.password = password; 
    
    }"""
        
    if verbose:
        print("All tests passed!")
    

def test_is_position_within_method(verbose=True):
    # TODO: Add more test cases
    
    if verbose:
        print("All tests passed!")
    
    
def test_all():
    test_extract_java_methods(verbose=False)
    test_is_position_within_method(verbose=False)
    
    print("All tests passed!")
    

if __name__ == '__main__':
    # test_summarize()
    test_extract_java_methods()