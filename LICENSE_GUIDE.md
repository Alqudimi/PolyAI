# License Guide

> **Repository:** https://github.com/Alqudimi/PolyAI

---

## PolyAI License

PolyAI itself is released under the **MIT License**. See [LICENSE](LICENSE) for the full text.

### What MIT Means

| You can… | Details |
|---|---|
| ✅ Use commercially | Build paid products with PolyAI |
| ✅ Modify | Change the source code |
| ✅ Distribute | Include PolyAI in your software |
| ✅ Use privately | Internal tools, scripts |
| ✅ Sublicense | Include in other licenses |

| You must… | Details |
|---|---|
| 📋 Include copyright | Keep the `Copyright (c) 2026 Abdulaziz Alqudimi` notice |
| 📋 Include license | Include the MIT license text in distributions |

| You cannot… | Details |
|---|---|
| ❌ Hold author liable | No warranty or liability from the author |
| ❌ Use author's name for endorsement | Cannot imply the author endorses your product |

---

## Provider License Considerations

PolyAI integrates with four providers. Each has its own terms:

### OVHcloud AI Endpoints
- **PolyAI usage:** MIT ✅
- **Provider terms:** [OVHcloud Terms of Service](https://www.ovhcloud.com/en/terms-and-conditions/)
- **Commercial use:** ✅ Permitted with a valid OVHcloud account
- **Data residency:** EU by default — check OVHcloud's data processing agreement

### Pollinations.AI
- **PolyAI usage:** MIT ✅
- **Provider terms:** [Pollinations Terms](https://pollinations.ai/terms)
- **Commercial use:** ✅ Permitted
- **Note:** Anonymous requests may be logged by the provider

### mlvoca
- **PolyAI usage:** MIT ✅
- **Provider terms:** [mlvoca Terms](https://mlvoca.com)
- **Commercial use:** ❌ **NON-COMMERCIAL ONLY**
- **Action required:** Do not use the `mlvoca` provider in commercial products

> ⚠️ **Warning:** Using mlvoca in a commercial context violates their terms of service. PolyAI makes this technically possible but does not endorse it. Use `provider="ovhcloud"` or `provider="pollinations"` for commercial applications.

### DevToolbox API
- **PolyAI usage:** MIT ✅
- **Provider terms:** [DevToolbox Terms](https://devtoolbox-api.devtoolbox-api.workers.dev)
- **Commercial use:** ✅ Permitted

---

## AI-Generated Content

Output from AI models may be subject to the provider's content policies. Consider:

1. **Copyright of AI output** — varies by jurisdiction; consult legal counsel for commercial use
2. **Content policies** — providers may restrict certain types of generated content
3. **User attribution** — if you display AI-generated content to users, consider disclosure

---

## Dependency Licenses

PolyAI's single production dependency:

| Package | License | Notes |
|---|---|---|
| `httpx` | BSD 3-Clause | Permissive — compatible with MIT |

All development dependencies are permissive licenses (MIT, BSD, Apache 2.0).

---

## FAQ

**Can I use PolyAI in a closed-source commercial product?**
Yes. MIT allows this. You must include the copyright notice in your software.

**Do I need to open-source my code if I use PolyAI?**
No. MIT does not require you to open-source your application (unlike GPL).

**Can I build a SaaS product using PolyAI?**
Yes, as long as you comply with each provider's terms and do not use mlvoca commercially.

**Can I modify PolyAI and distribute my modified version?**
Yes. You must keep the MIT license and copyright notice in your distribution.
