"""Compare saved motion features with an offline replay, without posting input."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics

POINTER_TYPES = {1, 2, 3, 4, 5, 6, 7, 25, 26, 27}


def motion(data):
    points = []
    for record in data["records"]:
        if record.get("origin") != "app-event" or record.get("type") not in POINTER_TYPES:
            continue
        coordinates = record.get("point")
        if not isinstance(coordinates, list) or len(coordinates) != 2:
            raise ValueError("Pointer record requires two coordinates")
        values = [record.get("timestampSeconds"), *coordinates]
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in values):
            raise ValueError("Motion values must be finite numbers")
        timestamp, x, y = values
        if points and timestamp < points[-1][0]:
            raise ValueError("Motion timestamps must not decrease")
        points.append((timestamp, x, y, record["type"]))
    if len(points) < 3:
        raise ValueError("At least three pointer records are required")
    start, x0, y0, _ = points[0]
    return [(t - start, x - x0, y - y0, kind) for t, x, y, kind in points]


def features(points):
    intervals = []
    distances = []
    speeds = []
    turns = []
    vectors = []
    for previous, current in zip(points, points[1:]):
        dt = current[0] - previous[0]
        dx, dy = current[1] - previous[1], current[2] - previous[2]
        distance = math.hypot(dx, dy)
        intervals.append(dt)
        distances.append(distance)
        if dt > 0:
            speeds.append(distance / dt)
        if distance > 0:
            vectors.append((dx, dy, distance))
    for a, b in zip(vectors, vectors[1:]):
        cosine = max(-1, min(1, (a[0] * b[0] + a[1] * b[1]) / (a[2] * b[2])))
        turns.append(math.acos(cosine))
    displacement = math.hypot(points[-1][1] - points[0][1], points[-1][2] - points[0][2])
    path = sum(distances)
    return {"sampleCount": len(points), "durationSeconds": points[-1][0],
            "pathPixels": path, "displacementPixels": displacement,
            "pathRatio": path / displacement if displacement else None,
            "meanSpeedPixelsPerSecond": statistics.mean(speeds) if speeds else None,
            "speedDeviation": statistics.pstdev(speeds) if speeds else None,
            "meanTurnRadians": statistics.mean(turns) if turns else None,
            "maximumGapSeconds": max(intervals)}


def summarize(path):
    payload = path.read_bytes()
    data = json.loads(payload)
    metadata = {"inputSHA256": hashlib.sha256(payload).hexdigest(),
                "humanBaselineVerified": data.get("humanBaselineVerified") is True,
                "acceptedFakeActions": data.get("acceptedFakeActions", 0)}
    try:
        trajectory = motion(data)
    except ValueError as error:
        return {**metadata, "motionAvailable": False, "reason": str(error)}
    # The replay copies behavior only. Source labels, IDs, and event metadata are absent.
    replay = [tuple(row) for row in trajectory]
    original_features = features(trajectory)
    replay_features = features(replay)
    return {**metadata, "motionAvailable": True,
            "features": original_features,
            "offlineReplayFeaturesEqual": original_features == replay_features}


def run(physical, synthetic, output):
    declared = summarize(physical)
    if not declared["motionAvailable"]:
        raise ValueError("Declared physical sample has no usable motion")
    comparisons = []
    for path in sorted(synthetic.glob("*.observations.json")):
        comparisons.append({"sample": path.stem, **summarize(path)})
    result = {"declaredPhysicalSample": declared, "syntheticSamples": comparisons,
              "physicalSessionCount": 1, "classifierTrained": False,
              "inputReportsSent": 0, "liveReplayAttempted": False,
              "scope": "Offline feature comparison only. Replaying the observed behavior preserves these features. No live evasion, human false-block rate, or browser prevention result."}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"syntheticSamples": len(comparisons),
                      "offlineReplayFeaturesEqual": declared["offlineReplayFeaturesEqual"],
                      "humanBaselineVerified": declared["humanBaselineVerified"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--physical", type=Path, required=True)
    parser.add_argument("--synthetic", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.physical, args.synthetic, args.output)
