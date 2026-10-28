#include "ContentActivityProjection.h"
#include "WebCoreActivityEnum.h"
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>

static void require(bool condition, const char* description)
{
    if (!condition) {
        std::cerr << description << '\n';
        std::exit(EXIT_FAILURE);
    }
}

int main()
{
    using Activity = WebCore::ActivityState;
    using Policy = WebKit::ContentActivityPolicy;
    constexpr std::array protectedFlags { Activity::WindowIsActive, Activity::IsFocused,
        Activity::IsVisible, Activity::IsVisibleOrOccluded, Activity::IsInWindow };
    std::uint16_t protectedMask = 0;
    for (auto flag : protectedFlags)
        protectedMask |= static_cast<std::uint16_t>(flag);
    constexpr auto visuallyIdleMask = static_cast<std::uint16_t>(Activity::IsVisuallyIdle);
    protectedMask |= visuallyIdleMask;

    for (std::uint32_t raw = 0; raw <= UINT16_MAX; ++raw) {
        auto observed = static_cast<std::uint16_t>(raw);
        auto native = WebKit::projectContentActivity<Activity>(observed, Policy::Native);
        auto stable = WebKit::projectContentActivity<Activity>(observed, Policy::StableBrowsing);
        require(native == observed, "Native policy changed activity");
        for (auto flag : protectedFlags)
            require(stable & static_cast<std::uint16_t>(flag), "A protected activity flag is absent");
        require(!(stable & visuallyIdleMask), "Stable content became visually idle");
        require((stable & static_cast<std::uint16_t>(~protectedMask))
            == (observed & static_cast<std::uint16_t>(~protectedMask)), "A nonprotected flag changed");
        require(WebKit::projectContentActivity<Activity>(stable, Policy::StableBrowsing) == stable,
            "Projection is not idempotent");
    }
    std::cout << "Projection properties passed for 65,536 states in both modes; WebKit integration is not compiled.\n";
}
