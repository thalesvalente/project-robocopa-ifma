import com.google.gson.*;
import org.java_websocket.WebSocket;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.*;
import org.java_websocket.server.WebSocketServer;
import org.java_websocket.drafts.Draft_6455;
import java.io.*;
import java.net.*;
import java.nio.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

/** Trusted per-bot protocol gateway; never relays administrator messages. */
public final class ProtocolGate {
    static final int MAX=16384;
    static final Set<String> HANDSHAKE=Set.of("type","sessionId","name","version","authors","secret",
        "description","homepage","countryCodes","gameTypes","platform","programmingLang","debuggerAttached","isDroid","teamMemberName","teamMessageBatchVersion");
    static final Set<String> NUMBERS=Set.of("turnRate","gunTurnRate","radarTurnRate","targetSpeed","firepower");
    static final Set<String> FLAGS=Set.of("adjustGunForBodyTurn","adjustRadarForBodyTurn","adjustRadarForGunTurn","rescan","fireAssist");
    static final Set<String> COLORS=Set.of("bodyColor","turretColor","radarColor","bulletColor","scanColor","tracksColor","gunColor");
    static final Set<String> SERVER_TYPES=Set.of("ServerHandshake","GameStartedEventForBot","RoundStartedEvent",
        "TickEventForBot","SkippedTurnEvent","RoundEndedEventForBot","GameEndedEventForBot","GameAbortedEvent");
    static final AtomicInteger accepted=new AtomicInteger(), rejected=new AtomicInteger(), intents=new AtomicInteger();
    static synchronized void saveStats() {
        try { JsonObject o=new JsonObject();o.addProperty("accepted_bot_sessions",accepted.get());
            o.addProperty("rejected_front_messages",rejected.get());o.addProperty("forwarded_intents",intents.get());
            Files.writeString(Path.of("/tmp/gate-report.json"),o.toString()); }
        catch(IOException ignored){}
    }
    static final class Rule {
        final String name,peerSecret,backendSecret; String session; boolean authenticated;
        Rule(String n,String p,String b){name=n;peerSecret=p;backendSecret=b;}
        JsonObject inbound(String text) throws IOException {
            JsonObject in=Wire.parse(text,MAX);String type=Wire.type(in);
            if(!authenticated) {
                if(!type.equals("BotHandshake") || session==null)throw new IOException("BOT_HANDSHAKE_REQUIRED");
                if(!HANDSHAKE.containsAll(in.keySet()))throw new IOException("HANDSHAKE_FIELDS");
                if(!Wire.str(in,"sessionId").equals(session) || !Wire.str(in,"name").equals(name)
                    || !Wire.str(in,"version").equals("1.0") || !Wire.equalSecret(Wire.str(in,"secret"),peerSecret))
                    throw new IOException("BOT_IDENTITY_DENIED");
                if(in.has("isDroid") && !in.get("isDroid").isJsonNull() && in.get("isDroid").getAsBoolean())throw new IOException("DROID_DENIED");
                JsonObject safe=Wire.obj("BotHandshake");safe.addProperty("sessionId",session);
                safe.addProperty("name",name);safe.addProperty("version","1.0");safe.addProperty("secret",backendSecret);
                JsonArray authors=new JsonArray();authors.add("Official Tank Royale samples");safe.add("authors",authors);
                authenticated=true;return safe;
            }
            if(type.equals("BotReady") && in.size()==1)return Wire.obj("BotReady");
            if(!type.equals("BotIntent"))throw new IOException("NON_GAME_MESSAGE_DENIED");
            JsonObject out=Wire.obj("BotIntent");
            for(var e:in.entrySet()) {
                String key=e.getKey();JsonElement val=e.getValue();if(key.equals("type"))continue;
                if(NUMBERS.contains(key)) {
                    if(!val.isJsonPrimitive() || !val.getAsJsonPrimitive().isNumber())throw new IOException("NUMERIC_ACTION_REQUIRED");
                    double n=val.getAsDouble();if(!Double.isFinite(n) || Math.abs(n)>10000)throw new IOException("ACTION_BOUND");
                    if(key.equals("firepower")&&(n<0||n>3))throw new IOException("FIRE_BOUND");
                    out.add(key,val);
                } else if(FLAGS.contains(key)) {
                    if(!val.isJsonPrimitive()||!val.getAsJsonPrimitive().isBoolean())throw new IOException("FLAG_TYPE");out.add(key,val);
                } else if(COLORS.contains(key)) {
                    if(!val.isJsonPrimitive()||!val.getAsJsonPrimitive().isString()||!val.getAsString().matches("#?[0-9a-fA-F]{6}"))
                        throw new IOException("COLOR_TYPE");out.add(key,val);
                } else if(key.equals("teamMessages") && val.isJsonArray() && val.getAsJsonArray().isEmpty()) {
                    // No team channel exists in this fixed two-single-bot experiment.
                } else if(key.equals("stdOut")||key.equals("stdErr")) {
                    if(!val.isJsonPrimitive()||!val.getAsJsonPrimitive().isString()||val.getAsString().length()>1024)
                        throw new IOException("BOT_LOG_LIMIT");
                } else throw new IOException("INTENT_FIELD_DENIED");
            }
            return out;
        }
    }
    static final class Gate extends WebSocketServer {
        final String name,peerSecret,backendSecret,backendUrl;
        final ConcurrentHashMap<WebSocket,Relay> sessions=new ConcurrentHashMap<>();
        final AtomicInteger connections=new AtomicInteger();
        final CountDownLatch ready=new CountDownLatch(1);
        Gate(String bind,String n,String p,String b,String url) {
            super(new InetSocketAddress(bind,8765),1,List.of(new Draft_6455(List.of(),List.of(),MAX)));
            name=n;peerSecret=p;backendSecret=b;backendUrl=url;setConnectionLostTimeout(10);setReuseAddr(false);
        }
        public void onOpen(WebSocket front,ClientHandshake h) {
            if(connections.incrementAndGet()>1){connections.decrementAndGet();front.close(1008,"ONE_BOT_SESSION");return;}
            Relay r=new Relay(front,new Rule(name,peerSecret,backendSecret));sessions.put(front,r);r.connect();
        }
        public void onMessage(WebSocket front,String text) {
            Relay r=sessions.get(front);if(r==null){front.close(1008,"NO_SESSION");return;}
            synchronized(r.rule) { try {
                boolean was=r.rule.authenticated;JsonObject safe=r.rule.inbound(text);r.send(safe.toString());
                if(!was){accepted.incrementAndGet();saveStats();}
                else if(Wire.type(safe).equals("BotIntent")){intents.incrementAndGet();}
            } catch(Exception e){rejected.incrementAndGet();saveStats();front.close(1008,"GAME_PROTOCOL_DENIED");r.close();} }
        }
        public void onMessage(WebSocket f,ByteBuffer b){rejected.incrementAndGet();saveStats();f.close(1003,"TEXT_ONLY");}
        public void onClose(WebSocket front,int code,String why,boolean remote){Relay r=sessions.remove(front);
            if(r!=null){connections.decrementAndGet();r.close();saveStats();}}
        public void onError(WebSocket f,Exception e){if(f!=null)f.close(1011,"GATE_FAILURE");else ready.countDown();}
        public void onStart(){saveStats();ready.countDown();}
        final class Relay extends WebSocketClient {
            final WebSocket front;final Rule rule;
            Relay(WebSocket f,Rule r){super(URI.create(backendUrl),new Draft_6455(),null,4000);front=f;rule=r;}
            public void onOpen(ServerHandshake h){}
            public void onMessage(String text){synchronized(rule){try{
                JsonObject msg=Wire.parse(text,2*1024*1024);String type=Wire.type(msg);
                if(!SERVER_TYPES.contains(type))throw new IOException("SERVER_TYPE_DENIED");
                if(type.equals("ServerHandshake")){
                    if(rule.session!=null||!Wire.str(msg,"version").equals("1.4.0"))throw new IOException("ENGINE_VERSION");
                    rule.session=Wire.str(msg,"sessionId");
                }
                front.send(text);if(type.equals("GameEndedEventForBot"))saveStats();
            }catch(Exception e){front.close(1008,"BACKEND_PROTOCOL_DENIED");close();}}}
            public void onClose(int code,String why,boolean remote){front.close(1000,"BACKEND_CLOSED");}
            public void onError(Exception e){front.close(1011,"BACKEND_FAILURE");}
        }
    }
    public static void main(String[] args)throws Exception {
        Gate a=new Gate(Wire.env("BIND_A"),"Walls",Wire.env("FRONT_A"),Wire.env("BACKEND_SECRET"),Wire.env("BACKEND_URL"));
        Gate b=new Gate(Wire.env("BIND_B"),"Spin Bot",Wire.env("FRONT_B"),Wire.env("BACKEND_SECRET"),Wire.env("BACKEND_URL"));
        a.start();b.start();if(!a.ready.await(8,TimeUnit.SECONDS)||!b.ready.await(8,TimeUnit.SECONDS))throw new IOException("GATE_TIMEOUT");
        Files.writeString(Path.of("/tmp/gateway-ready"),"ready");new CountDownLatch(1).await();
    }
}
