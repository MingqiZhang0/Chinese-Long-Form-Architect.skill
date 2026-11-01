#if NOMINAL_NEGATIVE
using Workbench.Protocol;
internal static class NominalNegative
{
    static void Accept(CharacterId character) {}
    static void Rejected() => Accept(new FactId("F1"));
}
#endif
