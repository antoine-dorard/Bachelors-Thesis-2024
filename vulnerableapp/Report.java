import com.itextpdf.text.Document;
import com.itextpdf.text.DocumentException;
import com.itextpdf.text.Paragraph;
import com.itextpdf.text.pdf.PdfWriter;
import java.io.ByteArrayOutputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.List;

public class Report {
    public void generatePDFAndHash(String filename, List<String> userData) throws DocumentException, IOException, NoSuchAlgorithmException {
        Document document = new Document();
        ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
        PdfWriter.getInstance(document, byteArrayOutputStream);
        document.open();
        userData.forEach(data -> {
            try {
                document.add(new Paragraph(data));
            } catch (DocumentException e) {
                e.printStackTrace();
            }
        });
        document.close();

        // Get the PDF data
        byte[] pdfData = byteArrayOutputStream.toByteArray();

        // Write PDF data to file
        try (FileOutputStream fileOutputStream = new FileOutputStream(filename)) {
            fileOutputStream.write(pdfData);
        }

        // Compute hash of the PDF data
        String hash = computeHash(pdfData);

        // Optionally, write the hash to a separate file or include it in the PDF
        try (FileOutputStream hashStream = new FileOutputStream(filename + ".hash")) {
            hashStream.write(hash.getBytes());
        }
    }

    private String computeHash(byte[] data) throws NoSuchAlgorithmException {
        MessageDigest digest = MessageDigest.getInstance("SHA-1");
        byte[] encodedhash = digest.digest(data);
        StringBuilder hexString = new StringBuilder(2 * encodedhash.length);
        for (byte b : encodedhash) {
            String hex = Integer.toHexString(0xff & b);
            if(hex.length() == 1) hexString.append('0');
            hexString.append(hex);
        }
        return hexString.toString();
    }
}
