// Kigyűjti a natív szűrő-nyilvántartást: a filterdesc-nevekhez tartozó
// regisztrációs helyeket és az onnan hivatkozott függvényeket.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.data.*;
import ghidra.app.decompiler.*;
import java.util.*;

public class FilterRegistry extends GhidraScript {

    static final String[] NAMES = {
        "radtint","linblur","dir_sat","dir_brite","dir_sharp","autobacklight",
        "focalpixelate","shadow","whitept","gamma","contrast","colortemp",
        "blur","backlight","triple","triple2","triple3","colorfix","rainbow",
        "fill","autocontrast","autolight","autocolor","enhance","sepia","bw"
    };

    @Override
    public void run() throws Exception {
        Memory mem = currentProgram.getMemory();
        Listing listing = currentProgram.getListing();
        ReferenceManager refs = currentProgram.getReferenceManager();

        println("=== SZURO-NEV -> ADAT-CIM -> HIVATKOZO KOD ===");
        Map<String, List<Address>> found = new LinkedHashMap<>();

        DataIterator di = listing.getDefinedData(true);
        while (di.hasNext() && !monitor.isCancelled()) {
            Data d = di.next();
            Object v = d.getValue();
            if (!(v instanceof String)) continue;
            String s = ((String) v).trim();
            for (String n : NAMES) {
                if (s.equals(n)) {
                    found.computeIfAbsent(n, k -> new ArrayList<>()).add(d.getAddress());
                }
            }
        }

        DecompInterface dec = new DecompInterface();
        dec.openProgram(currentProgram);

        for (String n : NAMES) {
            List<Address> addrs = found.get(n);
            if (addrs == null) { println("\n-- " + n + ": NINCS definialt sztring"); continue; }
            println("\n-- " + n + "  (" + addrs.size() + " sztring-elofordulas)");
            for (Address a : addrs) {
                println("   sztring @ " + a);
                ReferenceIterator ri = refs.getReferencesTo(a);
                int c = 0;
                while (ri.hasNext() && c < 6) {
                    Reference r = ri.next();
                    Address from = r.getFromAddress();
                    Function f = getFunctionContaining(from);
                    println("     <- " + from + (f != null ? ("  fv: " + f.getName() + " @ " + f.getEntryPoint()) : "  (adat)"));
                    // ha adat-hivatkozas, nezzuk meg a kornyezetet: kovetkezo 8 duplaszo
                    if (f == null) {
                        StringBuilder sb = new StringBuilder("        rekord: ");
                        for (int k = -2; k < 8; k++) {
                            try {
                                Address p = from.add(k * 4L);
                                long w = mem.getInt(p) & 0xffffffffL;
                                sb.append(String.format("%08x ", w));
                            } catch (Exception e) { sb.append("........ "); }
                        }
                        println(sb.toString());
                    }
                    c++;
                }
                if (c == 0) println("     (nincs hivatkozas)");
            }
        }
        dec.dispose();
        println("\n=== VEGE ===");
    }
}
