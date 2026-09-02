// A teljes program kereshető, determinisztikus CSV-indexét exportálja.
// A kinyert szöveget adatként kezeli; semmit nem hajt végre belőle.
import ghidra.app.script.GhidraScript;
import ghidra.framework.Application;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.DataIterator;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.mem.MemoryBlockSourceInfo;
import ghidra.program.model.symbol.ExternalLocation;
import ghidra.program.model.symbol.ExternalLocationIterator;
import ghidra.program.model.symbol.ExternalManager;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;
import ghidra.program.model.symbol.SymbolType;
import ghidra.program.model.symbol.SourceType;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

public class BinaryIndex extends GhidraScript {
    private static final String GHIDRA_VERSION = "12.1.2";
    private static final String[] OUTPUTS = {
        "functions.csv", "xrefs.csv", "string_xrefs.csv", "imports.csv",
        "rtti.csv", "data_symbols.csv", "meta.json",
    };
    // A kézzel és dekompilálással igazolt registry-belépési pontok. A Ghidra
    // ezek közül néhány szomszédos burkolót tévesen egy függvénybe olvaszt.
    private static final Object[][] KNOWN_CALLBACKS = {
        {"autobacklight", 0x008f7cc0L}, {"finetune", 0x008f7cf0L},
        {"finetune2", 0x008f7ee0L}, {"autolight", 0x008f80c0L},
        {"autocolor", 0x008f82a0L}, {"debug", 0x008f8360L},
        {"ansel", 0x008f8410L}, {"bw", 0x008f84c0L},
        {"radblur", 0x008f8520L}, {"radsat", 0x008f8680L},
        {"radtint", 0x008f8730L}, {"tilt", 0x008f8810L},
        {"enhance", 0x008f8840L}, {"grain|grain2", 0x008f88e0L},
        {"warm", 0x008f8930L}, {"sepia", 0x008f8950L},
        {"backlight|fill", 0x008f8970L}, {"blur", 0x008f89a0L},
        {"autocontrast", 0x008f89d0L}, {"contrast", 0x008f8a20L},
        {"triple", 0x008f8a60L}, {"triple2", 0x008f8b90L},
        {"triple3", 0x008f8ce0L}, {"gamma", 0x008f8e30L},
        {"colortemp", 0x008f8ea0L}, {"shadow", 0x008f8ee0L},
        {"unsharp|unsharp2", 0x008f8f30L}, {"glow|glow2", 0x008f8f70L},
        {"dir_sat", 0x008f8fb0L}, {"sat", 0x008f8ff0L},
        {"dir_brite", 0x008f9050L}, {"dir_sharp", 0x008f9090L},
        {"colorfix", 0x008f9190L}, {"whitept", 0x008f9270L},
        {"rainbow", 0x008f92d0L}, {"tint", 0x008f9630L},
        {"dir_tint", 0x008f9880L}, {"linblur", 0x008f99c0L},
    };
    private static final long CALLBACK_REGION_END = 0x008f9bc0L;

    private File outputDirectory;
    private File workingDirectory;
    private Listing listing;
    private Memory memory;
    private ReferenceManager references;
    private Address imageBase;
    private TreeMap<Long, String> knownCallbacks;

    private static final class RowWriter implements AutoCloseable {
        private final BufferedWriter writer;

        RowWriter(File file, String... header) throws Exception {
            writer = new BufferedWriter(new OutputStreamWriter(
                new FileOutputStream(file), StandardCharsets.UTF_8));
            row((Object[]) header);
        }

        void row(Object... values) throws Exception {
            for (int i = 0; i < values.length; i++) {
                if (i > 0) writer.write(',');
                String value = values[i] == null ? "" : values[i].toString();
                writer.write('"');
                writer.write(value.replace("\"", "\"\"").replace("\r\n", "\n").replace('\r', '\n'));
                writer.write('"');
            }
            writer.newLine();
        }

        @Override
        public void close() throws Exception {
            writer.close();
        }
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1 || args.length > 2
                || (args.length == 2 && !"picasa3".equals(args[1]))) {
            throw new IllegalArgumentException(
                "Használat: BinaryIndex.java <eredménykönyvtár> [picasa3]");
        }
        outputDirectory = new File(args[0]).getCanonicalFile();
        if (!outputDirectory.isDirectory() && !outputDirectory.mkdirs()) {
            throw new IllegalStateException("Nem hozható létre: " + outputDirectory);
        }
        String actualVersion = Application.getApplicationVersion();
        if (!GHIDRA_VERSION.equals(actualVersion)) {
            throw new IllegalStateException(
                "Nem várt Ghidra-verzió: " + actualVersion + " != " + GHIDRA_VERSION);
        }
        prepareAtomicExport();
        listing = currentProgram.getListing();
        memory = currentProgram.getMemory();
        references = currentProgram.getReferenceManager();
        imageBase = currentProgram.getImageBase();
        knownCallbacks = new TreeMap<>();
        if (args.length == 2) {
            for (Object[] callback : KNOWN_CALLBACKS) {
                knownCallbacks.put((Long)callback[1], (String)callback[0]);
            }
            materializeKnownCallbacks();
        }

        exportFunctions();
        exportReferences();
        exportStringReferences();
        exportImports();
        exportRtti();
        exportDataSymbols();
        exportMeta();
        monitor.checkCancelled();
        publishAtomicExport();
        println("BINARY_INDEX_OK " + outputDirectory);
    }

    private void materializeKnownCallbacks() throws Exception {
        // Az autoanalízis néhány rövid, egymás melletti burkolót összeolvaszt.
        // Csak a bizonyított registry-régiót bontjuk szét, majd minden ismert
        // belépési pontról újradiszasszemblálunk.
        for (long offset : knownCallbacks.keySet()) {
            monitor.checkCancelled();
            Address address = currentProgram.getAddressFactory().getDefaultAddressSpace()
                .getAddress(offset);
            if (listing.getFunctionAt(address) != null) continue;
            Function containing = listing.getFunctionContaining(address);
            if (containing != null) removeFunction(containing);
        }
        for (Map.Entry<Long, String> callback : knownCallbacks.entrySet()) {
            monitor.checkCancelled();
            Address address = currentProgram.getAddressFactory().getDefaultAddressSpace()
                .getAddress(callback.getKey());
            if (listing.getFunctionAt(address) != null) continue;
            disassemble(address);
            Function created = createFunction(address, "KNOWN_CALLBACK_" + callback.getValue());
            if (created == null) {
                throw new IllegalStateException("Nem materializálható callback: " + address);
            }
        }
    }

    private void prepareAtomicExport() throws Exception {
        workingDirectory = new File(outputDirectory, ".binary-index-part");
        if (!workingDirectory.isDirectory() && !workingDirectory.mkdirs()) {
            throw new IllegalStateException("Nem hozható létre: " + workingDirectory);
        }
        for (String name : OUTPUTS) {
            Files.deleteIfExists(new File(workingDirectory, name).toPath());
        }
    }

    private void publishAtomicExport() throws Exception {
        for (String name : OUTPUTS) {
            File source = new File(workingDirectory, name);
            if (!source.isFile()) throw new IllegalStateException("Hiányos export: " + source);
        }
        for (String name : OUTPUTS) {
            Files.move(
                new File(workingDirectory, name).toPath(),
                new File(outputDirectory, name).toPath(),
                StandardCopyOption.REPLACE_EXISTING,
                StandardCopyOption.ATOMIC_MOVE);
        }
        Files.deleteIfExists(workingDirectory.toPath());
    }

    private File outputFile(String name) {
        return new File(workingDirectory, name);
    }

    private long va(Address address) {
        return address.getOffset();
    }

    private long rva(Address address) {
        return address.getOffset() - imageBase.getOffset();
    }

    private Long fileOffset(Address address) {
        try {
            if (!memory.contains(address)) return null;
            // PE esetén a Ghidra eredeti fájlbájt-leképezése a bizonyító erejű.
            MemoryBlock block = memory.getBlock(address);
            if (block == null) return null;
            for (MemoryBlockSourceInfo source : block.getSourceInfos()) {
                if (!source.contains(address)) continue;
                long mapped = source.getFileBytesOffset(address);
                return mapped < 0 ? null : mapped;
            }
            return null;
        } catch (Exception ignored) {
            return null;
        }
    }

    private String section(Address address) {
        MemoryBlock block = memory.getBlock(address);
        return block == null ? "" : block.getName();
    }

    private Object[] addressColumns(Address address) {
        if (address == null || !address.isMemoryAddress()) return new Object[] {null, null, null};
        Long offset = fileOffset(address);
        return new Object[] {
            String.format("0x%08x", va(address)),
            String.format("0x%08x", rva(address)),
            offset == null ? null : String.format("0x%08x", offset),
        };
    }

    private void exportFunctions() throws Exception {
        final class FunctionRow {
            Address address; String name, callingConvention; long size; boolean thunk;
            FunctionRow(Address a, String n, long s, boolean t, String c) {
                address=a; name=n; size=s; thunk=t; callingConvention=c;
            }
        }
        TreeMap<Long, FunctionRow> rows = new TreeMap<>();
        FunctionIterator it = listing.getFunctions(true);
        while (it.hasNext()) {
            monitor.checkCancelled();
            Function f = it.next();
            rows.put(va(f.getEntryPoint()), new FunctionRow(
                f.getEntryPoint(), f.getName(), f.getBody().getNumAddresses(),
                f.isThunk(), f.getCallingConventionName()));
        }
        for (Map.Entry<Long, String> callback : knownCallbacks.entrySet()) {
            if (rows.containsKey(callback.getKey())) continue;
            Long next = knownCallbacks.higherKey(callback.getKey());
            long end = next == null ? CALLBACK_REGION_END : next;
            Address address = currentProgram.getAddressFactory().getDefaultAddressSpace()
                .getAddress(callback.getKey());
            rows.put(callback.getKey(), new FunctionRow(
                address, "KNOWN_CALLBACK_" + callback.getValue(),
                end - callback.getKey(), false, "unknown"));
        }
        ReferenceIterator calls = references.getReferenceIterator(imageBase);
        while (calls.hasNext()) {
            monitor.checkCancelled();
            Reference call = calls.next();
            if (!call.getReferenceType().isCall() || !call.getToAddress().isMemoryAddress()) {
                continue;
            }
            Address target = call.getToAddress();
            rows.putIfAbsent(va(target), new FunctionRow(
                target, "CALL_TARGET_" + target, 0, false, "unknown"));
        }
        try (RowWriter out = new RowWriter(outputFile("functions.csv"),
                "addr", "rva", "file_offset", "name", "size", "section", "is_thunk", "calling_conv")) {
            for (FunctionRow row : rows.values()) {
                Object[] a = addressColumns(row.address);
                out.row(a[0], a[1], a[2], row.name, row.size,
                    section(row.address), row.thunk, row.callingConvention);
            }
        }
    }

    private Address callbackOwner(Address callSite) {
        if (knownCallbacks.isEmpty()) return null;
        long offset = va(callSite);
        if (offset < knownCallbacks.firstKey() || offset >= CALLBACK_REGION_END) return null;
        Map.Entry<Long, String> owner = knownCallbacks.floorEntry(offset);
        if (owner == null) return null;
        return currentProgram.getAddressFactory().getDefaultAddressSpace()
            .getAddress(owner.getKey());
    }

    private String referenceType(Reference ref) {
        if (ref.getReferenceType().isCall()) return "call";
        if (ref.getReferenceType().isRead() && ref.getReferenceType().isWrite()) return "read_write";
        if (ref.getReferenceType().isRead()) return "read";
        if (ref.getReferenceType().isWrite()) return "write";
        if (ref.getReferenceType().isData()) return "data";
        if (ref.getReferenceType().isJump()) return "jump";
        return ref.getReferenceType().getName().toLowerCase().replace(' ', '_');
    }

    private void exportReferences() throws Exception {
        final class XrefRow {
            Address from, to; int count;
            XrefRow(Address f, Address t) { from=f; to=t; count=1; }
        }
        Map<String, XrefRow> unique = new LinkedHashMap<>();
        ReferenceIterator it = references.getReferenceIterator(imageBase);
        while (it.hasNext()) {
            monitor.checkCancelled();
            Reference ref = it.next();
            if (ref.getReferenceType().isCall()
                    && ref.getFromAddress().isMemoryAddress()
                    && ref.getToAddress().isMemoryAddress()) {
                Address from = callbackOwner(ref.getFromAddress());
                if (from == null) {
                    Function owner = listing.getFunctionContaining(ref.getFromAddress());
                    if (owner == null) continue;
                    from = owner.getEntryPoint();
                }
                Address to = ref.getToAddress();
                String key = from + ":" + to;
                XrefRow row = unique.get(key);
                if (row == null) unique.put(key, new XrefRow(from, to));
                else row.count++;
            }
        }
        List<XrefRow> rows = new ArrayList<>(unique.values());
        rows.sort(Comparator.comparingLong((XrefRow r) -> va(r.from))
            .thenComparingLong(r -> va(r.to)));
        try (RowWriter out = new RowWriter(outputFile("xrefs.csv"),
                "from_addr", "from_rva", "from_file_offset",
                "to_addr", "to_rva", "to_file_offset", "type", "call_count")) {
            for (XrefRow row : rows) {
                Object[] from = addressColumns(row.from);
                Object[] to = addressColumns(row.to);
                out.row(from[0], from[1], from[2], to[0], to[1], to[2], "call", row.count);
            }
        }
    }

    private void exportStringReferences() throws Exception {
        final class StringRow {
            Address stringAddress; String text; String encoding; Address functionAddress;
            StringRow(Address a, String t, String e, Address f) { stringAddress=a; text=t; encoding=e; functionAddress=f; }
        }
        List<StringRow> rows = new ArrayList<>();
        DataIterator data = listing.getDefinedData(true);
        while (data.hasNext()) {
            monitor.checkCancelled();
            Data item = data.next();
            Object value = item.getValue();
            if (!(value instanceof String)) continue;
            String encoding = item.getDataType().getName().toLowerCase().contains("unicode") ? "utf-16le" : "ascii";
            ReferenceIterator refs = references.getReferencesTo(item.getAddress());
            Set<Long> seen = new LinkedHashSet<>();
            while (refs.hasNext()) {
                Reference ref = refs.next();
                Function owner = listing.getFunctionContaining(ref.getFromAddress());
                if (owner != null && seen.add(va(owner.getEntryPoint()))) {
                    rows.add(new StringRow(item.getAddress(), (String)value, encoding, owner.getEntryPoint()));
                }
            }
        }
        rows.sort(Comparator.comparingLong((StringRow r) -> va(r.stringAddress))
            .thenComparingLong(r -> va(r.functionAddress)));
        try (RowWriter out = new RowWriter(outputFile("string_xrefs.csv"),
                "str_addr", "str_rva", "str_file_offset", "text", "encoding",
                "func_addr", "func_rva", "func_file_offset")) {
            for (StringRow row : rows) {
                Object[] s = addressColumns(row.stringAddress); Object[] f = addressColumns(row.functionAddress);
                out.row(s[0], s[1], s[2], row.text, row.encoding, f[0], f[1], f[2]);
            }
        }
    }

    private void exportImports() throws Exception {
        final class ImportRow {
            String dll, symbol; Address address, function;
            ImportRow(String d, String s, Address a, Address f) { dll=d; symbol=s; address=a; function=f; }
        }
        List<ImportRow> rows = new ArrayList<>();
        Set<String> seen = new LinkedHashSet<>();
        ExternalManager manager = currentProgram.getExternalManager();
        for (String library : manager.getExternalLibraryNames()) {
            monitor.checkCancelled();
            ExternalLocationIterator locations = manager.getExternalLocations(library);
            while (locations.hasNext()) {
                ExternalLocation location = locations.next();
                Address target = location.getAddress();
                Address referenceTarget = location.getExternalSpaceAddress();
                ReferenceIterator refs = references.getReferencesTo(referenceTarget);
                boolean referenced = false;
                while (refs.hasNext()) {
                    Reference ref = refs.next();
                    Function owner = listing.getFunctionContaining(ref.getFromAddress());
                    Address function = owner == null ? null : owner.getEntryPoint();
                    String key = library + "\u0000" + location.getLabel() + "\u0000" + function;
                    if (seen.add(key)) rows.add(new ImportRow(
                        library, location.getLabel(), target, function));
                    referenced = true;
                }
                if (!referenced) {
                    String key = library + "\u0000" + location.getLabel() + "\u0000";
                    if (seen.add(key)) rows.add(new ImportRow(
                        library, location.getLabel(), target, null));
                }
            }
        }
        rows.sort(Comparator.comparing((ImportRow r) -> r.dll).thenComparing(r -> r.symbol)
            .thenComparingLong(r -> r.function == null ? Long.MAX_VALUE : va(r.function)));
        try (RowWriter out = new RowWriter(outputFile("imports.csv"),
                "dll", "symbol", "addr", "rva", "file_offset", "func_addr", "func_rva", "func_file_offset")) {
            for (ImportRow row : rows) {
                Object[] a = addressColumns(row.address); Object[] f = addressColumns(row.function);
                out.row(row.dll, row.symbol, a[0], a[1], a[2], f[0], f[1], f[2]);
            }
        }
    }

    private void exportRtti() throws Exception {
        List<Symbol> rows = new ArrayList<>();
        SymbolIterator symbols = currentProgram.getSymbolTable().getAllSymbols(true);
        while (symbols.hasNext()) {
            monitor.checkCancelled();
            Symbol symbol = symbols.next();
            String name = symbol.getName();
            if (name.startsWith("??_7") || (name.contains("vftable") && !name.contains("meta_ptr"))) {
                rows.add(symbol);
            }
        }
        rows.sort(Comparator.comparingLong(s -> va(s.getAddress())));
        try (RowWriter out = new RowWriter(outputFile("rtti.csv"),
                "class_name", "vtable_addr", "vtable_rva", "vtable_file_offset", "method_addrs")) {
            for (Symbol symbol : rows) {
                Address address = symbol.getAddress(); Object[] a = addressColumns(address);
                List<String> methods = new ArrayList<>();
                for (int i = 0; i < 256; i += currentProgram.getDefaultPointerSize()) {
                    try {
                        long pointer = memory.getInt(address.add(i)) & 0xffffffffL;
                        Address method = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(pointer);
                        if (listing.getFunctionAt(method) == null) break;
                        methods.add(String.format("0x%08x", pointer));
                    } catch (Exception e) { break; }
                }
                out.row(symbol.getName(true), a[0], a[1], a[2], String.join(";", methods));
            }
        }
    }

    private void exportDataSymbols() throws Exception {
        List<Symbol> rows = new ArrayList<>();
        SymbolIterator symbols = currentProgram.getSymbolTable().getAllSymbols(true);
        while (symbols.hasNext()) {
            monitor.checkCancelled();
            Symbol symbol = symbols.next();
            if (symbol.getSymbolType() == SymbolType.LABEL && memory.contains(symbol.getAddress())
                    && symbol.getSource() != SourceType.DEFAULT
                    && listing.getDataAt(symbol.getAddress()) != null
                    && listing.getFunctionAt(symbol.getAddress()) == null) rows.add(symbol);
        }
        rows.sort(Comparator.comparingLong(s -> va(s.getAddress())));
        try (RowWriter out = new RowWriter(outputFile("data_symbols.csv"),
                "addr", "rva", "file_offset", "name", "type", "size")) {
            for (Symbol symbol : rows) {
                Data item = listing.getDataAt(symbol.getAddress()); Object[] a = addressColumns(symbol.getAddress());
                out.row(a[0], a[1], a[2], symbol.getName(true), item == null ? "label" : item.getDataType().getName(),
                    item == null ? 0 : item.getLength());
            }
        }
    }

    private String sha256(File file) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (java.io.InputStream in = new java.io.FileInputStream(file)) {
            byte[] buffer = new byte[1024 * 1024]; int count;
            while ((count = in.read(buffer)) >= 0) digest.update(buffer, 0, count);
        }
        StringBuilder hex = new StringBuilder();
        for (byte b : digest.digest()) hex.append(String.format("%02x", b));
        return hex.toString();
    }

    private void exportMeta() throws Exception {
        File executable = currentProgram.getExecutablePath() == null ? null : new File(currentProgram.getExecutablePath());
        String hash = executable != null && executable.isFile() ? sha256(executable) : currentProgram.getExecutableSHA256();
        File file = outputFile("meta.json");
        String format = currentProgram.getExecutableFormat();
        try (BufferedWriter out = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(file), StandardCharsets.UTF_8))) {
            out.write("{\n");
            out.write("  \"binary_sha256\": \"" + hash + "\",\n");
            out.write("  \"ghidra_version\": \"" + jsonEscape(Application.getApplicationVersion()) + "\",\n");
            out.write("  \"image_base\": " + imageBase.getOffset() + ",\n");
            out.write("  \"language_id\": \"" + jsonEscape(currentProgram.getLanguageID().toString()) + "\",\n");
            out.write("  \"executable_format\": \"" + jsonEscape(format == null ? "" : format) + "\"\n");
            out.write("}\n");
        }
    }

    private String jsonEscape(String value) {
        StringBuilder result = new StringBuilder();
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            switch (c) {
                case '\"': result.append("\\\""); break;
                case '\\': result.append("\\\\"); break;
                case '\b': result.append("\\b"); break;
                case '\f': result.append("\\f"); break;
                case '\n': result.append("\\n"); break;
                case '\r': result.append("\\r"); break;
                case '\t': result.append("\\t"); break;
                default:
                    if (c < 0x20) result.append(String.format("\\u%04x", (int)c));
                    else result.append(c);
            }
        }
        return result.toString();
    }
}
