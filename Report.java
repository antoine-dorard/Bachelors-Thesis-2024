import com.itextpdf.text.Document;
import com.itextpdf.text.DocumentException;
import com.itextpdf.text.Paragraph;
import com.itextpdf.text.pdf.PdfWriter;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.SecretKeySpec;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.Map;

public class Report {
    private Map<String, String> data;

    public Report(Map<String, String> data) {
        this.data = data;
    }

    public void generatePDF(String filename) throws DocumentException, IOException {
        Document document = new Document();
        ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
        PdfWriter.getInstance(document, byteArrayOutputStream);
        document.open();
        data.forEach((key, value) -> {
            try {
                document.add(new Paragraph(key + ": " + value));
            } catch (DocumentException e) {
                e.printStackTrace();
            }
        });
        document.close();
        byte[] pdfContent = byteArrayOutputStream.toByteArray();
        byte[] encryptedContent = encryptDES(pdfContent);
        try (FileOutputStream fileOutputStream = new FileOutputStream(filename)) {
            fileOutputStream.write(encryptedContent);
        }
    }

    private byte[] encryptDES(byte[] inputData) {
        try {
            KeyGenerator keyGenerator = KeyGenerator.getInstance("DES");
            keyGenerator.init(56); // DES is limited to 56-bit key size
            SecretKey key = keyGenerator.generateKey();
            Cipher cipher = Cipher.getInstance("DES/ECB/PKCS5Padding");
            cipher.init(Cipher.ENCRYPT_MODE, key);
            return cipher.doFinal(inputData);
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

    public static void main(String[] args) {
        Map<String, String> reportData = Map.of(
                "Title", "Annual Report 2023",
                "Author", "Jane Doe",
                "Summary", "This is an annual summary report."
        );
        Report report = new Report(reportData);
        try {
            report.generatePDF("EncryptedReport.pdf");
        } catch (DocumentException | IOException e) {
            e.printStackTrace();
        }
    }
}
