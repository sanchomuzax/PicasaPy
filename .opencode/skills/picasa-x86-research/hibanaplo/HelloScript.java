// Minimális headless betöltési kontroll.
import ghidra.app.script.GhidraScript;

public class HelloScript extends GhidraScript {
    @Override
    public void run() throws Exception {
        println("PICASAPY_GHIDRA_SCRIPT_OK");
    }
}
