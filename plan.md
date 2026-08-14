# Projekt asystenta AI do planowania lekcji i czatbota edukacyjnego

Najpierw należy zebrać wszystkie materiały dydaktyczne – slajdy PDF, podręczniki robotyki, notatki nauczycieli – i zamienić je na tekst. W praktyce robi się to za pomocą OCR, np. usługi Azure Document Intelligence (Read OCR), która potrafi wyciągnąć tekst i strukturę z dokumentów PDF. Po konwersji warto oczyścić dane (usunąć nagłówki, numerację stron itp.) i podzielić tekst na sensowne fragmenty (np. pojedyncze slajdy lub akapity) wraz z metadanymi (temat, tytuł lekcji, numer slajdu).

## Baza wiedzy wektorowej

Następnie tworzy się bazę wektorową z przygotowanych fragmentów. Każdy tekst (np. zawartość slajdu) zamieniamy na wektor (embedding) za pomocą modelu semantycznego – np. Azure OpenAI Embedding API lub otwartego modelu LLM. Takie wektory przechowujemy w bazie wektorowej (np. Azure AI Search z opcją wektorową lub innym serwisie typu Pinecone/Weaviate/Qdrant). Dzięki temu można wyszukiwać fragmenty o podobnej treści na podstawie zapytania w postaci wektora. Taki pipeline został pokazany w poradnikach: najpierw wyciągamy tekst (OCR), potem generujemy wektory, a następnie indeksujemy je w serwisie wyszukiwania.

- **Kroki:** chunking – dzielenie dokumentów na mniejsze kawałki, generowanie embeddingów – konwersja tekstu na wektor, indeksowanie – zapis wektorów do bazy.
- **Technologie:** Azure OpenAI (embeddings), Azure AI Search (wyszukiwanie wektorowe), inne: Pinecone, Weaviate, Qdrant, itp. Korzystając z Azure, wszystkie elementy (OCR, embedding, wyszukiwanie) da się zintegrować w chmurze.

## Asystent AI dla nauczyciela

Głównym zadaniem asystenta jest wspomaganie nauczyciela przy przygotowywaniu lekcji. Nauczyciel mógłby zadawać mu pytania typu: „Jakie są główne cele lekcji z tego tematu?”, „Podaj plan lekcji na podstawie tych materiałów”, „Wymień kluczowe punkty omawiane na slajdach”. System wtedy wyszukuje w bazie wektorów fragmenty odpowiadające zapytaniu (np. „cele lekcji programowania w Pythonie”) i używa modelu językowego (GPT) do sformułowania odpowiedzi czy planu zajęć. Dzięki temu odpowiedzi będą oparte na konkretnych slajdach i notatkach, a nie tylko wyimaginowane przez model. To podejście Retrieval-Augmented Generation (RAG) pozwala **uzasadnić odpowiedź konkretnymi źródłami** i zredukować błędy. Jak podkreślają specjaliści, system RAG wyszukuje istotne informacje w dokumentach przed wygenerowaniem odpowiedzi, co sprawia, że odpowiedzi są aktualne, dokładne i weryfikowalne.

- **Strategia budowy:** zaczynamy od prostego prototypu – np. chatbot wyszukujący fragmenty i generujący podsumowania. Następnie iteracyjnie poprawiamy prompt (treść instrukcji dla modelu) i ewentualnie dobieramy model (GPT-4, GPT-4o, Llama3 itp.) na podstawie testów. Można zacząć od większego modelu (np. GPT-4 przez Azure OpenAI) dla lepszej jakości, a później rozważyć tańsze lub lokalne modele (Llama 3, Mistral) dla niższych kosztów.
- **Przykład działania:** nauczyciel pyta: „Co uczniowie powinni zrozumieć z tej lekcji?”, agent wyszukuje fragmenty mówiące o celach lekcji i generuje listę punktów. Każda odpowiedź powinna odnosić się do konkretnych materiałów, aby nauczyciel wiedział, że model „tylko powtarza” zawartość, a nie wymyśla.

## Chatbot dla uczniów

Po uruchomieniu dla nauczyciela można stopniowo udostępnić system uczniom jako chatbota edukacyjnego. Uczniowie mogliby zadawać pytania dotyczące materiału z zajęć (np. „Jak działa ten program w Pythonie na slajdach?”), a chatbot odsyłałby do odpowiednich fragmentów notatek lub tłumaczył je prostszym językiem. Tu wymagana jest dodatkowa uwaga na formułowanie odpowiedzi przyjaznych młodszym użytkownikom oraz możliwe filtrowanie (by chatbot nie podpowiadał ściągania czy nie wykładał się nieodpowiednio). Pod kątem technicznym korzystamy z tej samej bazy wektorowej: model traktuje pytania uczniów podobnie jak nauczyciela, ale prompt i ton wypowiedzi mogą być łagodniejsze i bardziej edukacyjne.

- **Integracja:** chatbot można wdrożyć jako osobny interfejs (np. aplikację webową lub bota na platformie edukacyjnej), korzystający z tego samego pipeline’u RAG co wersja dla nauczyciela. 
- **Strategia wdrożenia:** najpierw upewnij się, że narzędzie działa dobrze z nauczycielami (poprawność odpowiedzi), potem rozszerz gamę zapytań i stylistykę dla uczniów. Warto przeprowadzić testy pilotażowe z rzeczywistymi uczniami, aby zebrać feedback.

## Metryki i ocena jakości

Dobry AI-asystent wymaga mierzenia skuteczności. Można tu zastosować kilka metryk:

- **Dokładność odpowiedzi („accuracy”):** jeśli przygotujesz dla kilku lekcji (np. 4–5) zbiór prawidłowych celów lub odpowiedzi (ground truth) ustalonych ręcznie przez nauczyciela, to potem obliczasz odsetek poprawnych odpowiedzi robota w porównaniu z tym zbiorem. 
- **Precyzja i recall w wyszukiwaniu:** mierzą, czy system znajduje właściwe slajdy/fragmenty związane z zapytaniem. Na przykład czy wśród kilku pobranych fragmentów przynajmniej połowa jest istotna (precision) i czy trafiliśmy we wszystkie potrzebne fragmenty (recall). Te miary dają obraz jakości części „wyszukiwarka” w architekturze RAG. Zazwyczaj liczy się też F1 score – średnią ważoną precision i recall.
- **Jakość generacji:** możemy użyć też miar typu BLEU/ROUGE do oceny podobieństwa generowanej odpowiedzi do tekstu wzorcowego, choć w praktyce ważniejsze jest subiektywne sprawdzenie przez ekspertów (nauczycieli). Często robi się też ewaluację z udziałem ludzi – nauczyciele oceniają czy odpowiedzi były pomocne, zrozumiałe i poprawne merytorycznie.

Dobrym pomysłem jest zbudowanie prostego zestawu testowego (np. zbiór pytań i poprawnych odpowiedzi dla kilku lekcji). Robot odpowiada na te pytania, a następnie automatycznie obliczasz np. procent poprawnych wyborów lub trafień. W badaniach nad systemami RAG podkreśla się, że **precyzja**, **recall** oraz **odsetek poprawnych odpowiedzi** to kluczowe wskaźniki jakości.

## Wdrożenie i monitorowanie na Azure

Ponieważ celem jest chmura Azure, możesz wykorzystać tamtejsze usługi:

- **OCR i ekstrakcja tekstu:** Azure Document Intelligence (zwany dawniej Form Recognizer) do rozpoznawania tekstu ze skanów/slajdów.
- **Baza wektorów:** Azure AI Search ma wektorowy tryb pracy, idealny do przechowywania embeddingów i szybkiego wyszukiwania semantycznego. Alternatywnie Pinecone czy Qdrant zainstalowane na Azure.
- **Model językowy:** Azure OpenAI (GPT-4, GPT-4o lub inne) do generowania odpowiedzi. Możesz też użyć lokalnego modelu (przez Azure Machine Learning lub virtual machine), np. Llama 3/Mistral, aby uniknąć stałych opłat za API.
- **Interfejs chatbota:** np. Azure Bot Service lub prosta aplikacja na Azure Web Apps, która wysyła zapytania do bazy wektorów i modelu. Dokumentacja pokazuje, że połączenie Web Apps + Bot Framework ułatwia budowę konwersacyjnych interfejsów.
- **CI/CD:** Automatyzację wdrożeń można osiągnąć przez Azure DevOps lub GitHub Actions. Narzędzia Azure Developer CLI (azd) pozwalają skonfigurować aplikację i zasoby chmurowe skryptem, co ułatwia powtarzalne wdrożenia. Należy też zadbać o wersjonowanie i testy kodu (np. testy integracyjne).
- **Monitorowanie:** warto włączyć Azure Monitor i Application Insights, aby śledzić zużycie zasobów, liczbę zapytań, błędy itp. Azure OpenAI udostępnia metryki (toks / zapytania) w Azure Monitor. Dzięki temu zobaczysz obciążenie systemu, czasy odpowiedzi, a przy spadku jakości też łatwiej zareagujesz.

## Harmonogram prac i strategie

Realizacja takiego projektu zwykle trwa kilka miesięcy dla pojedynczej osoby, zwłaszcza jeśli to pierwsze doświadczenie z AI. Przykładowo, zespoły często dzielą pracę na fazy: 

- **Faza 1 – Planowanie i zbieranie wymagań (1–2 tygodnie):** analiza potrzeb nauczycieli, przegląd materiałów, decyzja o narzędziach (OCR, wektorowa baza, model LLM).  
- **Faza 2 – Przygotowanie danych (2–4 tygodnie):** OCR wszystkich dokumentów, czyszczenie tekstu, dzielenie na chunk'i, generowanie embeddingów i ich indeksowanie. To bardzo czasochłonna część – często niedoszacowywana.  
- **Faza 3 – Budowa prototypu chatbota (2–4 tygodnie):** stworzenie backendu, który przyjmuje zapytania, wyszukuje w bazie wektorowej i wywołuje model językowy (prompt engineering). Tutaj testuje się różne konstrukcje promptów i sprawdza odpowiedzi.  
- **Faza 4 – Ewaluacja i tuning (1–2 tygodnie):** ocena wyników na przykładowych pytaniach, poprawki w promptach i ewentualnie w modelach. Tworzenie wspomnianego zbioru ground-truth (poprawne odpowiedzi/czynniki lekcji) dla kilkunastu pytań do automatycznego testu.  
- **Faza 5 – Wdrożenie i testy integracyjne (1–2 tygodnie):** publikacja na platformie Azure, konfiguracja ciągłej integracji, testy obciążeniowe, sprawdzenie bezpieczeństwa i monitorowania.  
- **Faza 6 – Udoskonalanie i feedback (ciągłe):** po uruchomieniu zbieramy opinie od nauczycieli/uczniów, dopisujemy nowe materiały, tune'ujemy system.

Ogólnie, doświadczeni specjaliści szacują, że prosty chatbot RAG wymaga **6–10 tygodni** pracy. Dla jednej osoby pracującej 6h/dzień (ok. 30h/tydz.) i uczącej się technologii może to być bliżej **3–4 miesięcy**. Dobrym pomysłem jest podzielenie projektu na fazy (MVP → rozbudowa) oraz korzystanie ze sprawdzonych narzędzi (np. gotowych API Azure). 

- **Wsparcie AI:** Korzystanie z asystentów kodowania (ChatGPT, Copilot itp.) może przyspieszyć naukę i rozwiązanie problemów technicznych. Na przykład pytanie o kod do parsowania PDF czy przygotowania bazy wektorowej.
- **Iteracyjne podejście:** Twórz najpierw wersję minimalną: np. agent odpowiadający tylko na dwa-trzy typy pytań. Później dodawaj funkcje: analiza slajdów, generowanie quizów, itd.
- **Bezpieczeństwo i etyka:** Zadbaj o anonimowość danych uczniów, filtrowanie nieodpowiednich treści, informowanie użytkowników o ograniczeniach chatbota.
- **Mierzenie postępów:** Co tydzień weryfikuj, czy system osiąga założoną dokładność. Dobrze jest widzieć procent poprawnych odpowiedzi na testowych zestawach pytań.

Podsumowując: kluczem jest **dobry pipeline przetwarzania dokumentów (OCR + indeksacja)** oraz **graniczenie roli modelu językowego do generacji na podstawie przetworzonych danych**. Metryki (precision/recall, accuracy) pozwolą ocenić efektywność, a przemyślana organizacja prac i korzystanie z usług Azure przyspieszy wdrożenie.

**Źródła:** Opis architektury RAG i praktyk pipeline’u – Infoservices; przydatność Azure Document Intelligence; przykładowe fazy i czas projektu RAG oraz typowe miary jakości RAG.

## Strategia — żeby nie utonąć
- Zacznij od 1 przedmiotu, nie od wszystkich. Weź jeden przedmiot z kilkunastoma slajdami, przejdź cały pipeline end-to-end, zanim dorzucisz resztę materiałów. Szybciej znajdziesz błędy na małej skali.
- Eval dataset rób na samym początku, nie na końcu. Bez niego nie wiesz czy Twoje zmiany w promptach/chunkingu w ogóle pomagają, czy tylko Ci się wydaje.
- Nie buduj chatbota dla uczniów, dopóki agent dla nauczyciela nie działa dobrze. To ten sam fundament, ale ryzyko (złe odpowiedzi dzieciom) jest dużo wyższe — najpierw upewnij się, że retrieval + generacja są solidne na mniej wymagającym użytkowniku (nauczycielu, który zweryfikuje odpowiedź).
- Nie kombinuj z frameworkami na starcie. LangChain/LlamaIndex kuszą, ale dla pierwszego projektu AI prostszy, "ręcznie napisany" pipeline (wywołania API wprost) jest łatwiejszy do zrozumienia i debugowania niż framework z dużą liczbą abstrakcji, których jeszcze nie znasz. Możesz dodać framework później, jak już rozumiesz co się dzieje pod spodem.
- Traktuj agenta AI (np. Claude Code) jako pomoc w pisaniu/debugowaniu kodu, nie jako osobę podejmującą decyzje architektoniczne za Ciebie. Największa wartość z Twojej strony to decyzje typu "co ma znaleźć się w chunku", "jaki prompt dla dzieci", "co uznajemy za dobrą odpowiedź" — to wymaga zrozumienia domeny (szkoła robotyki), a nie samego kodowania.
- Loguj wszystko od początku (jakie pytanie, jakie fragmenty zwrócił retrieval, jaka odpowiedź) — to Ci ułatwi debugowanie i pokaże administracji/na obronie projektu, jak system faktycznie działa.
