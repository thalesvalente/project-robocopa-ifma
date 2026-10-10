import com.google.gson.*;
import com.google.gson.stream.*;
import java.io.*;
import java.net.URI;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.*;

/** Strict bounded JSON and WebSocket helpers; no dynamic command execution. */
public final class Wire {
    public static JsonObject parse(String text, int maxBytes) throws IOException {
        if (text.getBytes(StandardCharsets.UTF_8).length > maxBytes) throw new IOException("MESSAGE_LIMIT");
        try (JsonReader r = new JsonReader(new StringReader(text))) {
            r.setLenient(false);
            JsonElement v = read(r, 0);
            if (!v.isJsonObject() || r.peek() != JsonToken.END_DOCUMENT) throw new IOException("OBJECT_REQUIRED");
            return v.getAsJsonObject();
        } catch (RuntimeException e) { throw new IOException("INVALID_JSON"); }
    }
    private static JsonElement read(JsonReader r, int depth) throws IOException {
        if (depth > 10) throw new IOException("JSON_DEPTH");
        switch(r.peek()) {
            case BEGIN_OBJECT: {
                r.beginObject(); JsonObject o=new JsonObject(); Set<String> keys=new HashSet<>();
                while(r.hasNext()) { String k=r.nextName(); if(!keys.add(k)) throw new IOException("DUPLICATE_KEY");
                    o.add(k,read(r,depth+1)); if(keys.size()>64) throw new IOException("KEY_LIMIT"); }
                r.endObject(); return o;
            }
            case BEGIN_ARRAY: {
                r.beginArray(); JsonArray a=new JsonArray();
                while(r.hasNext()) { a.add(read(r,depth+1)); if(a.size()>512) throw new IOException("ARRAY_LIMIT"); }
                r.endArray(); return a;
            }
            case STRING: return new JsonPrimitive(r.nextString());
            case BOOLEAN: return new JsonPrimitive(r.nextBoolean());
            case NULL: r.nextNull(); return JsonNull.INSTANCE;
            case NUMBER: {
                String n=r.nextString(); double d=Double.parseDouble(n);
                if(!Double.isFinite(d)) throw new IOException("FINITE_NUMBER_REQUIRED");
                return new JsonPrimitive(new java.math.BigDecimal(n));
            }
            default: throw new IOException("JSON_TYPE");
        }
    }
    public static String str(JsonObject o,String k) throws IOException {
        JsonElement v=o.get(k);
        if(v==null || !v.isJsonPrimitive() || !v.getAsJsonPrimitive().isString()) throw new IOException("STRING_REQUIRED");
        return v.getAsString();
    }
    public static String type(JsonObject o) throws IOException { return str(o,"type"); }
    public static JsonObject obj(String type) { JsonObject o=new JsonObject();o.addProperty("type",type);return o; }
    public static boolean equalSecret(String a,String b) {
        return java.security.MessageDigest.isEqual(a.getBytes(StandardCharsets.UTF_8),b.getBytes(StandardCharsets.UTF_8));
    }
    public static String env(String k) {
        String v=System.getenv(k); if(v==null || v.isEmpty()) throw new IllegalArgumentException("MISSING_CONFIG");return v;
    }
    public static final class Client implements WebSocket.Listener,AutoCloseable {
        private final BlockingQueue<String> queue=new ArrayBlockingQueue<>(1024);
        private final StringBuilder buffer=new StringBuilder();
        private volatile int closed=0; private volatile boolean error=false;
        private WebSocket ws;
        public Client(String url) {
            ws=HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(4)).build()
                .newWebSocketBuilder().connectTimeout(Duration.ofSeconds(4))
                .buildAsync(URI.create(url),this).orTimeout(5,TimeUnit.SECONDS).join();
        }
        @Override public void onOpen(WebSocket w) { w.request(1); }
        @Override public CompletionStage<?> onText(WebSocket w,CharSequence s,boolean last) {
            buffer.append(s);
            if(buffer.length()>2*1024*1024) {error=true;w.abort();return null;}
            if(last) { if(!queue.offer(buffer.toString())) { error=true;w.abort(); } buffer.setLength(0); }
            w.request(1); return null;
        }
        @Override public CompletionStage<?> onClose(WebSocket w,int code,String reason) {closed=code;return null;}
        @Override public void onError(WebSocket w,Throwable t) {error=true;}
        public void send(JsonObject o) {send(o.toString());}
        public void send(String s) { ws.sendText(s,true).orTimeout(4,TimeUnit.SECONDS).join(); }
        public String take(long milliseconds) throws Exception {
            long deadline=System.nanoTime()+TimeUnit.MILLISECONDS.toNanos(milliseconds);
            while(System.nanoTime()<deadline) {
                String s=queue.poll(30,TimeUnit.MILLISECONDS);if(s!=null)return s;
                if(closed!=0 || error)throw new IOException("SOCKET_CLOSED");
            }
            throw new IOException("MESSAGE_TIMEOUT");
        }
        public int awaitClose() throws Exception {
            for(int i=0;i<150 && closed==0 && !error;i++)Thread.sleep(20);
            return closed;
        }
        public JsonObject handshake(String role,String secret) throws Exception {
            JsonObject h=parse(take(5000),65536);
            if(!type(h).equals("ServerHandshake") || !str(h,"version").equals("1.4.0"))throw new IOException("ENGINE_HANDSHAKE");
            JsonObject r=obj(role);r.addProperty("sessionId",str(h,"sessionId"));
            r.addProperty("name","RoboCopa-I2");r.addProperty("version","0.1");r.addProperty("secret",secret);
            send(r);return h;
        }
        @Override public void close(){if(ws!=null)ws.abort();}
    }
    private Wire(){}
}
